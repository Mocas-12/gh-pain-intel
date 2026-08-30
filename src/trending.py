"""每日 Star 增幅榜：解析 GitHub 官方 Trending 页的当日新增星标（stars today）。

GitHub Search API 只能按“总星数”排序，拿不到“今天涨了多少星”；而 GitHub Trending
页面（https://github.com/trending?since=daily）由官方统计每个仓库最近一天的新增
星标数，是“每日增幅”唯一的权威数据源，因此这里直接抓取并解析该页面 HTML。

注意：Trending 页面自身的排序混合了 GitHub 的其他热度信号，并不严格等于增幅
数值排序，所以解析后需按 “stars today” 重新降序排列。

缓存策略：按 UTC 日期落盘（.cache/trending_daily_YYYY-MM-DD.json），
同一天内重复打开应用直接读缓存，跨天自动重新抓取并清理旧文件。
页面抓取不消耗 GitHub API 配额，也无需 Token。
"""
from __future__ import annotations

import html as html_lib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

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
    now = now or datetime.now(timezone.utc)
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


def get_star_gainers(force: bool = False, timeout: int = 20) -> list[dict]:
    """获取今日 Star 增幅 Top 10：优先读当日缓存，否则抓取 Trending 页并落盘。

    Raises RuntimeError 当请求失败或页面解析为空时（由调用方决定如何降级展示）。
    """
    tag = day_tag()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"trending_daily_{tag}.json"

    if cache_file.exists() and not force:
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (OSError, json.JSONDecodeError):
            pass  # 缓存损坏则重新抓取

    resp = requests.get(
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
    return data
