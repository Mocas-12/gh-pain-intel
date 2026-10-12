"""每日 Star 增幅榜：解析 GitHub 官方 Trending 页的当日新增星标（stars today）。

GitHub Search API 只能按“总星数”排序，拿不到“今天涨了多少星”；而 GitHub Trending
页面（https://github.com/trending?since=daily）由官方统计每个仓库最近一天的新增
星标数，是“每日增幅”唯一的权威数据源，因此这里直接抓取并解析该页面 HTML。

注意：Trending 页面自身的排序混合了 GitHub 的其他热度信号，并不严格等于增幅
数值排序，所以解析后需按 “stars today” 重新降序排列。

缓存策略：按 UTC 日期落盘（.cache/trending_daily_YYYY-MM-DD.json），
同一天内重复打开应用直接读缓存，跨天自动重新抓取并清理旧文件。
另有上榜历史快照（trending_history.json，滚动 15 天），用于给榜单标注
「NEW（昨日未上榜）/ 连续 N 天上榜」，冷启动首日无基线不标记。
Topics 标签（trending_topics_日期.json，当日缓存）从各仓库页面 About 栏
并发抓取，让访客不点进 GitHub 也能知道项目是干嘛的；均为页面抓取，
不消耗 GitHub API 配额，也无需 Token。
"""
from __future__ import annotations

import html as html_lib
import json
import os
import re
from datetime import datetime, timedelta, UTC
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

# 模块级会话：复用底层连接池（行为不变，仅避免每次请求重建连接）
_SESSION = requests.Session()

GITHUB_TRENDING_URL = "https://github.com/trending"
TOP_N = 10
CACHE_DIR = Path(
    os.environ.get("PAIN_INTEL_CACHE_DIR", str(Path(__file__).resolve().parent.parent / ".cache"))
)

# 用浏览器 UA 请求 github.com 的 HTML 页面（非 API），避免被当作机器人拦截
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def day_tag(now: datetime | None = None) -> str:
    """当前 UTC 时间对应的日期标签，如 '2026-08-24'。"""
    now = now or datetime.now(UTC)
    return now.strftime("%Y-%m-%d")


def _clean_text(fragment: str) -> str:
    """去掉简介里的内嵌标签与 HTML 实体，压缩空白。"""
    text = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


def parse_trending_html(page_html: str) -> list[dict]:
    """解析 Trending 页 HTML，按当日新增星标降序返回榜单条目（最多 10 条）。

    每条包含 repo / stars(总星数) / gained(当日新增) / language / description / url。
    没有 “stars today” 数字的行不参与增幅排序，直接跳过。
    """
    out: list[dict] = []
    for article in re.split(r"<article", page_html)[1:]:
        m_repo = re.search(
            r'<h2[^>]*>.*?href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)["?#]', article, re.S
        )
        if not m_repo:
            continue
        full_name = m_repo.group(1)
        m_total = re.search(
            rf'href="/{re.escape(full_name)}/stargazers"[^>]*>(?:\s*<[^>]+>)*\s*([\d,]+)',
            article,
        )
        m_gain = re.search(r"([\d,]+)\s+stars?\s+today", article)
        if m_gain is None:
            continue
        m_lang = re.search(r'itemprop="programmingLanguage">([^<]+)<', article)
        m_desc = re.search(r'<p class="[^"]*col-9[^"]*">(.*?)</p>', article, re.S)
        out.append(
            {
                "repo": full_name,
                "stars": int(m_total.group(1).replace(",", "")) if m_total else 0,
                "gained": int(m_gain.group(1).replace(",", "")),
                "language": m_lang.group(1).strip() if m_lang else "-",
                "description": _clean_text(m_desc.group(1)) if m_desc else "",
                "url": f"https://github.com/{full_name}",
            }
        )
    out.sort(key=lambda r: -r["gained"])
    return out[:TOP_N]


def _history_path() -> Path:
    """上榜历史快照文件（按天滚动，记录每天的 repo 名单）。"""
    return CACHE_DIR / "trending_history.json"


def _load_history() -> dict[str, list[str]]:
    try:
        data = json.loads(_history_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _record_history(repos: list[str], tag: str) -> None:
    """把当日榜单 repo 名单写入历史（幂等 upsert），保留最近 15 天。"""
    history = _load_history()
    history[tag] = sorted(set(repos))
    trimmed = {k: history[k] for k in sorted(history)[-15:]}
    try:
        _history_path().write_text(
            json.dumps(trimmed, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass  # 历史写入失败不影响榜单返回


def _days_on_board(history: dict[str, list[str]], repo: str, tag: str) -> int | None:
    """repo 的连续上榜天数（含今天）；无早于今天的历史时返回 None（冷启动不标记）。

    容忍一天空洞：某日应用没被打开导致的缺档不断开连续计数。
    """
    try:
        today = datetime.strptime(tag, "%Y-%m-%d").date()
    except ValueError:
        return None
    valid = {}
    for key in history:
        try:
            valid[datetime.strptime(key, "%Y-%m-%d").date()] = set(history[key])
        except ValueError:
            continue
    earlier = [d for d in valid if d < today]
    if not earlier:
        return None
    days, gap_used = 1, False
    d = today - timedelta(days=1)
    while d >= min(earlier):
        if d in valid:
            if repo in valid[d]:
                days += 1
            else:
                break
        elif not gap_used:
            gap_used = True  # 单日缺档，跳过继续看更早
        else:
            break
        d -= timedelta(days=1)
    return days


def _topics_path(tag: str) -> Path:
    """当日 topics 缓存文件（repo → 标签列表）。"""
    return CACHE_DIR / f"trending_topics_{tag}.json"


def _load_topics(tag: str) -> dict[str, list[str]]:
    try:
        data = json.loads(_topics_path(tag).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _fetch_topics(repos: list[str], tag: str) -> dict[str, list[str]]:
    """并发抓取各仓库页面的 About 栏 topic 标签（页面抓取，不消耗 API 配额）。

    当日缓存，缺失的仓库才发请求；单个仓库失败留空不影响榜单。
    """
    cached = _load_topics(tag)
    todo = [r for r in repos if r not in cached]
    if todo:
        def one(repo: str) -> tuple[str, list[str]]:
            try:
                resp = _SESSION.get(
                    f"https://github.com/{repo}", headers=BROWSER_HEADERS, timeout=10
                )
                if resp.status_code == 200:
                    seen: set[str] = set()
                    topics: list[str] = []
                    for t in re.findall(r'href="/topics/([A-Za-z0-9\-]+)"', resp.text):
                        if t not in seen:
                            seen.add(t)
                            topics.append(t)
                    return repo, topics[:6]
            except requests.RequestException:
                pass  # 单仓失败留空
            return repo, []

        with ThreadPoolExecutor(max_workers=4) as pool:
            for repo, topics in pool.map(one, todo):
                cached[repo] = topics
        try:
            _topics_path(tag).write_text(
                json.dumps(cached, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass  # 缓存写入失败不影响本次返回
    return cached


def _finalize(data: list[dict], tag: str) -> list[dict]:
    """给榜单附加连续上榜天数与 topics 标签，并登记当日名单进历史。"""
    history = _load_history()
    for r in data:
        r["days_on_board"] = _days_on_board(history, r["repo"], tag)
    topics = _fetch_topics([r["repo"] for r in data], tag)
    for r in data:
        r["topics"] = topics.get(r["repo"], [])
    _record_history([r["repo"] for r in data], tag)
    return data


def get_star_gainers(force: bool = False) -> list[dict]:
    """获取今日 Star 增幅 Top 10：优先读当日缓存，否则抓取 Trending 页并落盘。

    force=True 时跳过当日缓存直接重新抓取（成功后覆盖缓存文件，失败则保留旧缓存）。
    返回的每条数据带 days_on_board 字段（连续上榜天数，None=无历史基线）。
    Raises RuntimeError 当请求失败或页面解析为空时（由调用方决定如何降级展示）。
    """
    timeout = 20
    tag = day_tag()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"trending_daily_{tag}.json"

    if not force and cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return _finalize(data, tag)
        except (OSError, json.JSONDecodeError):
            pass  # 缓存损坏则重新抓取

    resp = _SESSION.get(
        GITHUB_TRENDING_URL,
        params={"since": "daily"},
        headers=BROWSER_HEADERS,
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub Trending 页面返回 HTTP {resp.status_code}")
    data = parse_trending_html(resp.text)
    if not data:
        raise RuntimeError("GitHub Trending 页面解析结果为空（页面结构可能已调整）")

    try:
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        for old in CACHE_DIR.glob("trending_daily_*.json"):  # 清理历史日期的缓存文件
            if old.name != cache_file.name:
                try:
                    old.unlink()
                except OSError:
                    pass
    except OSError:
        pass  # 缓存写入失败不影响本次结果返回
    return _finalize(data, tag)


def last_updated() -> datetime | None:
    """当日榜单缓存的落盘时间（近似最近一次抓取时间）；尚无缓存时返回 None。"""
    cache_file = CACHE_DIR / f"trending_daily_{day_tag()}.json"
    try:
        return datetime.fromtimestamp(cache_file.stat().st_mtime)
    except OSError:
        return None
