"""数据抓取层：通过 GitHub REST API 抓取指定仓库最近 N 天的 Issues。

- 仅做只读抓取，用于内部情报分析，不向平台写入任何内容；
- 未配置 Token 时使用匿名配额（60 次/小时），配置后提升至 5000 次/小时；
- 自带限流退避（Retry-After）、PR 过滤与讨论热度排序。
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

import requests

GITHUB_API = "https://api.github.com"
PER_PAGE = 100


@dataclass
class Issue:
    """一条 Issue 的规范化文本载体（供后续 LLM 分析）。"""

    repo: str
    number: int
    title: str
    body: str
    state: str
    labels: list[str]
    comments_count: int
    reactions: int
    created_at: str
    updated_at: str
    url: str
    comments: list[str] = field(default_factory=list)

    @property
    def flat_text(self) -> str:
        """拼接后的分析文本（截断，防止超出模型上下文）。"""
        label_txt = ",".join(self.labels) or "-"
        comment_txt = "\n".join(f"- {c}" for c in self.comments[:5])
        body = (self.body or "").strip()[:1200]
        return (
            f"[{self.repo}#{self.number}] {self.title}\n"
            f"labels: {label_txt} | reactions:{self.reactions} | comments:{self.comments_count}\n"
            f"{body}\n"
            f"热门评论:\n{comment_txt[:800]}"
        )

    def to_dict(self) -> dict:
        return asdict(self)


class GitHubClient:
    """带限流退避的极简 GitHub REST 客户端。"""

    def __init__(self, token: str | None = None):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "gh-pain-intel/0.1",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, url: str, params: dict | None = None, max_retry: int = 3) -> requests.Response:
        """GET，遇 403/429 按 Retry-After 退避重试。"""
        resp = None
        for attempt in range(max_retry):
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code in (403, 429):  # 触发限流
                wait = int(resp.headers.get("Retry-After", 5 * (attempt + 1)))
                time.sleep(min(wait, 60))
                continue
            return resp
        assert resp is not None
        return resp

    def fetch_comments(self, repo: str, number: int, limit: int = 5) -> list[str]:
        """抓取单条 Issue 的前几条评论作为语境。"""
        resp = self._get(f"{GITHUB_API}/repos/{repo}/issues/{number}/comments", {"per_page": 20})
        if resp.status_code != 200:
            return []
        out: list[str] = []
        for c in resp.json():
            body = (c.get("body") or "").strip().replace("\n", " ")
            if body:
                out.append(body[:300])
            if len(out) >= limit:
                break
        return out

    def fetch_repo_issues(
        self,
        repo: str,
        days: int = 7,
        max_issues: int = 200,
        include_comments: bool = True,
        progress_cb: Callable[[str], None] | None = None,
    ) -> list[Issue]:
        """抓取单个仓库近 `days` 天内更新的 Issues（排除 Pull Request）。"""
        log = progress_cb or (lambda msg: None)
        since = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).isoformat(timespec="seconds").replace("+00:00", "Z")

        issues: list[Issue] = []
        page = 1
        while len(issues) < max_issues and page <= 20:  # 页数安全上限
            params = {
                "state": "all",
                "since": since,
                "per_page": PER_PAGE,
                "page": page,
                "sort": "updated",
                "direction": "desc",
            }
            resp = self._get(f"{GITHUB_API}/repos/{repo}/issues", params)
            if resp.status_code == 404:
                raise ValueError(f"仓库不存在或无权访问: {repo}")
            if resp.status_code != 200:
                raise RuntimeError(f"GitHub API 错误 {resp.status_code}: {resp.text[:200]}")
            batch = resp.json()
            if not batch:
                break
            for item in batch:
                if "pull_request" in item:  # 排除 PR
                    continue
                issues.append(
                    Issue(
                        repo=repo,
                        number=item["number"],
                        title=item.get("title") or "",
                        body=item.get("body") or "",
                        state=item.get("state", "open"),
                        labels=[lb["name"] for lb in item.get("labels", [])],
                        comments_count=item.get("comments", 0),
                        reactions=(item.get("reactions") or {}).get("total_count", 0),
                        created_at=item.get("created_at", ""),
                        updated_at=item.get("updated_at", ""),
                        url=item.get("html_url", ""),
                    )
                )
                if len(issues) >= max_issues:
                    break
            page += 1

        # 按讨论热度排序（评论 + 反应），优先保留最有信息量的样本
        issues.sort(key=lambda i: i.comments_count + i.reactions, reverse=True)
        issues = issues[:max_issues]

        # 匿名配额紧张时压缩补评论的数量
        budget = 60 if "Authorization" in self.session.headers else 12
        if include_comments:
            for iss in issues[:budget]:
                iss.comments = self.fetch_comments(iss.repo, iss.number)

        log(f"{repo}: 抓取到 {len(issues)} 条 Issue（窗口 {days} 天）")
        return issues


def fetch_many(
    client: GitHubClient,
    repos: list[str],
    *,
    days: int = 7,
    max_per_repo: int = 120,
    include_comments: bool = True,
    progress_cb: Callable[[str], None] | None = None,
) -> tuple[list[Issue], list[str]]:
    """批量抓取多个仓库，返回 (全部 Issue, 错误信息列表)。"""
    all_issues: list[Issue] = []
    errors: list[str] = []
    for repo in [r.strip() for r in repos if r.strip()]:
        try:
            got = client.fetch_repo_issues(repo, days, max_per_repo, include_comments, progress_cb)
            all_issues.extend(got)
        except Exception as exc:  # 单仓失败不影响整体
            errors.append(f"{repo}: {exc}")
    return all_issues, errors
