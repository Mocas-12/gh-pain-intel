"""热门仓库榜单：每天自动更新的 GitHub 高星活跃仓库 Top 10。

数据源为 GitHub Search API（独立搜索配额，本功能每天仅真实请求一次）。
缓存策略：按 UTC 日期落盘（.cache/hot_repos_YYYY-MM-DD.json），
同一天内重复打开应用直接读缓存，跨天自动重新拉取并清理旧文件。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
CACHE_DIR = Path(
    os.environ.get("PAIN_INTEL_CACHE_DIR", str(Path(__file__).resolve().parent.parent / ".cache"))
)


def day_tag(now: datetime | None = None) -> str:
    """当前 UTC 时间对应的日期标签，如 '2026-08-24'。"""
    now = now or datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d")


def parse_search_response(items: list) -> list[dict]:
    """把 GitHub 搜索结果解析为紧凑的榜单条目列表（最多 10 条）。"""
    out: list[dict] = []
    for it in items[:10]:
        out.append(
            {
                "repo": it.get("full_name", ""),
                "stars": int(it.get("stargazers_count", 0)),
                "description": (it.get("description") or "").strip(),
                "language": it.get("language") or "-",
                "url": it.get("html_url", ""),
            }
        )
    return out


def get_hot_repos(token: str | None = None, force: bool = False, timeout: int = 15) -> list[dict]:
    """获取本周热门仓库 Top 10：优先读当周缓存，否则请求 API 并落盘。

    Raises RuntimeError 当请求失败时（由调用方决定如何降级展示）。
    """
    tag = day_tag()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"hot_repos_{tag}.json"

    if cache_file.exists() and not force:
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (OSError, json.JSONDecodeError):
            pass  # 缓存损坏则重新拉取

    since = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "gh-pain-intel/0.1",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(
        GITHUB_SEARCH_URL,
        params={
            "q": f"stars:>3000 pushed:>{since}",
            "sort": "stars",
            "order": "desc",
            "per_page": 10,
        },
        headers=headers,
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub 搜索接口返回 HTTP {resp.status_code}")
    data = parse_search_response(resp.json().get("items", []))

    try:
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        for old in CACHE_DIR.glob("hot_repos_*.json"):  # 清理历史日期的缓存文件
            if old.name != cache_file.name:
                try:
                    old.unlink()
                except OSError:
                    pass
    except OSError:
        pass  # 缓存写入失败不影响本次结果返回
    return data
