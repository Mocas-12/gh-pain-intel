"""抓取层单元测试：用假会话覆盖分页、PR 过滤、热度排序、评论预算与错误路径（离线）。"""
from __future__ import annotations

import time
import unittest
from unittest import mock

import requests

from src.scraper import GitHubClient, GitHubRateLimitError, fetch_many


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else []
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._payload


class FakeSession:
    """按 handler(url, params) 分发的假会话，记录全部 GET 调用。"""

    def __init__(self, handler):
        self.handler = handler
        self.headers = {}
        self.calls: list[str] = []

    def get(self, url, params=None, timeout=None):
        self.calls.append(url)
        return self.handler(url, params)


def gh_issue(num: int, comments: int = 0, reactions: int = 0, pr: bool = False) -> dict:
    item = {
        "number": num,
        "title": f"issue {num}",
        "body": "body",
        "state": "open",
        "labels": [],
        "comments": comments,
        "reactions": {"total_count": reactions},
        "created_at": "",
        "updated_at": "",
        "html_url": f"http://x/{num}",
    }
    if pr:
        item["pull_request"] = {}
    return item


def issues_handler(pages: list[list[dict]]):
    """返回按页码分发 Issue 列表的 handler；页码超出 pages 后返回空页。"""
    def handler(url: str, params=None):
        if url.endswith("/issues"):
            page = (params or {}).get("page", 1)
            return FakeResponse(payload=pages[page - 1] if page <= len(pages) else [])
        return FakeResponse(payload=[{"body": "a comment"}])
    return handler


def make_client(handler, token: str | None = None) -> tuple[GitHubClient, FakeSession]:
    client = GitHubClient(token=token)
    fake = FakeSession(handler)
    client.session = fake
    if token:
        fake.headers["Authorization"] = f"Bearer {token}"
    return client, fake


class FetchRepoIssuesTest(unittest.TestCase):
    def test_prs_filtered_and_sorted_by_heat(self):
        page = [
            gh_issue(1, comments=0, reactions=0),
            gh_issue(2, comments=99, pr=True),   # PR 应被剔除
            gh_issue(3, comments=5, reactions=10),
            gh_issue(4, comments=1, reactions=0),
        ]
        client, _ = make_client(issues_handler([page]))
        issues = client.fetch_repo_issues("o/r", include_comments=False)
        self.assertEqual([i.number for i in issues], [3, 4, 1])  # 热度 15 > 1 > 0；PR #2 已剔除

    def test_pagination_stops_on_empty_page(self):
        client, fake = make_client(
            issues_handler([[gh_issue(1)], [gh_issue(2)]])  # 第二页有数据，第三页为空
        )
        issues = client.fetch_repo_issues("o/r", include_comments=False)
        self.assertEqual(len(issues), 2)
        issue_pages = [u for u in fake.calls if u.endswith("/issues") and "/comments" not in u]
        self.assertEqual(len(issue_pages), 3)  # 抓了两页 + 探空的第三页

    def test_max_issues_keeps_hottest(self):
        page = [gh_issue(1, comments=1), gh_issue(2, comments=10), gh_issue(3, comments=5)]
        client, _ = make_client(issues_handler([page]))
        issues = client.fetch_repo_issues("o/r", max_issues=2, include_comments=False)
        self.assertEqual([i.number for i in issues], [2, 3])

    def test_anonymous_comment_budget_is_tighter(self):
        page = [gh_issue(i, comments=1) for i in range(15)]
        anon_client, anon_fake = make_client(issues_handler([page]), token=None)
        anon_client.fetch_repo_issues("o/r", include_comments=True)
        anon_calls = [u for u in anon_fake.calls if u.endswith("/comments")]

        auth_client, auth_fake = make_client(issues_handler([page]), token="t")
        auth_client.fetch_repo_issues("o/r", include_comments=True)
        auth_calls = [u for u in auth_fake.calls if u.endswith("/comments")]

        self.assertEqual(len(anon_calls), 12)  # 匿名预算 12
        self.assertEqual(len(auth_calls), 15)  # 认证预算 60，未触及

    def test_comment_fetch_aborts_budget_on_rate_limit(self):
        page = [gh_issue(1), gh_issue(2)]

        def handler(url: str, params=None):
            if url.endswith("/comments"):
                return FakeResponse(status_code=403, headers={"X-RateLimit-Remaining": "0"})
            if (params or {}).get("page", 1) == 1:
                return FakeResponse(payload=page)
            return FakeResponse(payload=[])

        client, fake = make_client(handler, token="t")
        issues = client.fetch_repo_issues("o/r", include_comments=True)
        self.assertEqual(len(issues), 2)  # 配额耗尽保留已抓结果
        self.assertLessEqual(len([u for u in fake.calls if u.endswith("/comments")]), 1)


class ErrorPathTest(unittest.TestCase):
    def test_404_raises_valueerror(self):
        client, _ = make_client(lambda url, params=None: FakeResponse(status_code=404, text="nf"))
        with self.assertRaises(ValueError):
            client.fetch_repo_issues("o/r")

    def test_other_error_raises_runtimeerror(self):
        client, _ = make_client(lambda url, params=None: FakeResponse(status_code=418, text="teapot"))
        with self.assertRaises(RuntimeError):
            client.fetch_repo_issues("o/r")

    def test_core_rate_limit_raises_fast_with_reset(self):
        reset_at = int(time.time()) + 600
        client, _ = make_client(lambda url, params=None: FakeResponse(
            status_code=403,
            headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset_at)},
        ))
        with self.assertRaises(GitHubRateLimitError) as ctx:
            client.fetch_repo_issues("o/r")
        self.assertAlmostEqual(ctx.exception.reset_epoch, reset_at, delta=1)

    def test_429_retries_then_succeeds(self):
        responses = iter([
            FakeResponse(status_code=429, headers={"Retry-After": "0"}),
            FakeResponse(payload=[gh_issue(1)]),
            FakeResponse(payload=[]),
        ])
        client, _ = make_client(lambda url, params=None: next(responses))
        with mock.patch("src.scraper.time.sleep") as sleep_mock:
            issues = client.fetch_repo_issues("o/r", include_comments=False)
        self.assertEqual([i.number for i in issues], [1])
        sleep_mock.assert_called()

    def test_rate_limit_endpoint_and_network_failure(self):
        def ok_handler(url: str, params=None):
            if url.endswith("/rate_limit"):
                return FakeResponse(payload={"resources": {"core": {
                    "limit": 5000, "remaining": 4999, "reset": 123}}})
            return FakeResponse()

        client, _ = make_client(ok_handler, token="t")
        quota = client.rate_limit()
        self.assertEqual(quota["remaining"], 4999)
        self.assertTrue(quota["authenticated"])

        def broken_handler(url: str, params=None):
            raise requests.ConnectionError("offline")

        client2, _ = make_client(broken_handler)
        self.assertEqual(client2.rate_limit(), {})


class FetchManyTest(unittest.TestCase):
    def test_single_repo_failure_is_isolated(self):
        client = GitHubClient(token="t")

        def fake_fetch(repo, *args, **kwargs):
            if repo == "bad/repo":
                raise ValueError("仓库不存在或无权访问: bad/repo")
            return []

        with mock.patch.object(client, "fetch_repo_issues", side_effect=fake_fetch):
            issues, errors = fetch_many(client, ["good/repo", "bad/repo"])
        self.assertEqual(issues, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("bad/repo", errors[0])

    def test_rate_limit_aborts_whole_batch(self):
        client = GitHubClient(token="t")
        with mock.patch.object(
            client, "fetch_repo_issues", side_effect=GitHubRateLimitError("耗尽")
        ):
            with self.assertRaises(GitHubRateLimitError):
                fetch_many(client, ["a/b", "c/d"])


if __name__ == "__main__":
    unittest.main()
