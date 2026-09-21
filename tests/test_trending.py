"""每日 Star 增幅榜的离线单元测试（不打网络）。"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, UTC
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.trending as trending
from src.trending import day_tag, parse_trending_html


def article(repo: str, stars: int, gained: int, lang: str = "Python", desc: str = "A test repo") -> str:
    """构造一个最小可解析的 Trending 页面仓库行。"""
    return f"""
    <article class="Box-row">
      <h2 class="h3 lh-condensed"><a href="/{repo}">{repo}</a></h2>
      <p class="col-9 color-fg-muted my-1 pr-4">{desc}</p>
      <div>
        <a class="link-muted d-inline-block mr-3" href="/{repo}/stargazers">
          <svg class="octicon octicon-star"></svg>{stars:,}
        </a>
        <span class="d-inline-block float-sm-right">
          <svg class="octicon octicon-star"></svg><span>{gained:,} stars today</span>
        </span>
        <span itemprop="programmingLanguage">{lang}</span>
      </div>
    </article>
    """


class DayTagTest(unittest.TestCase):
    def test_known_date(self):
        self.assertEqual(day_tag(datetime(2026, 8, 24, tzinfo=UTC)), "2026-08-24")

    def test_year_boundary(self):
        self.assertEqual(day_tag(datetime(2027, 1, 1, tzinfo=UTC)), "2027-01-01")


class ParseTrendingHtmlTest(unittest.TestCase):
    def test_sorts_by_gained_desc_and_extracts_fields(self):
        page = "<html>" + article("a/low", 1000, 12) + article("b/high", 2000, 300) + "</html>"
        rows = parse_trending_html(page)
        self.assertEqual([r["repo"] for r in rows], ["b/high", "a/low"])
        self.assertEqual(rows[0]["gained"], 300)
        self.assertEqual(rows[0]["stars"], 2000)
        self.assertEqual(rows[0]["url"], "https://github.com/b/high")
        self.assertEqual(rows[0]["language"], "Python")
        self.assertEqual(rows[0]["description"], "A test repo")

    def test_page_order_is_not_trusted(self):
        # 页面把 907 星的排在 3,730 星前面（GitHub 混合了其他热度信号），解析后必须按数值重排
        page = "<html>" + article("o/first", 90000, 907) + article("o/second", 33000, 3730) + "</html>"
        rows = parse_trending_html(page)
        self.assertEqual(rows[0]["repo"], "o/second")

    def test_caps_at_ten(self):
        page = "<html>" + "".join(article(f"o/r{i}", 100, i) for i in range(15)) + "</html>"
        rows = parse_trending_html(page)
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0]["gained"], 14)
        self.assertEqual(rows[-1]["gained"], 5)

    def test_skips_rows_without_gained(self):
        page = (
            "<html>"
            + article("o/ok", 100, 5)
            + '<article><h2><a href="/o/nogain">x</a></h2></article>'
            + "</html>"
        )
        rows = parse_trending_html(page)
        self.assertEqual([r["repo"] for r in rows], ["o/ok"])

    def test_missing_language_and_description(self):
        page = (
            "<html><article>"
            '<h2><a href="/o/r">r</a></h2><span>5 stars today</span>'
            "</article></html>"
        )
        rows = parse_trending_html(page)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["language"], "-")
        self.assertEqual(rows[0]["description"], "")
        self.assertEqual(rows[0]["stars"], 0)

    def test_description_strips_inner_tags_and_entities(self):
        page = "<html>" + article("o/r", 100, 5, desc="Fast &amp; <em>tiny</em>  lib") + "</html>"
        rows = parse_trending_html(page)
        self.assertEqual(rows[0]["description"], "Fast & tiny lib")

    def test_empty_html_returns_empty(self):
        self.assertEqual(parse_trending_html("<html></html>"), [])


class GetStarGainersCacheTest(unittest.TestCase):
    """磁盘缓存与 force 语义：False 读缓存、True 绕过重抓、失败保留旧缓存。

    看板的「🔄 刷新」按钮依赖 force=True 穿透当日磁盘缓存（当日缓存与
    Streamlit 内存缓存双层结构见 src/trending.py 模块注释），这里是契约测试。
    """

    def setUp(self):
        self._orig_dir = trending.CACHE_DIR
        self._tmp = tempfile.mkdtemp()
        trending.CACHE_DIR = Path(self._tmp)

    def tearDown(self):
        trending.CACHE_DIR = self._orig_dir
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _seed(self) -> Path:
        cache = trending.CACHE_DIR / f"trending_daily_{trending.day_tag()}.json"
        cache.write_text(
            json.dumps([{"repo": "fake/repo", "stars": 1, "gained": 1,
                         "language": "Py", "description": "", "url": "#"}]),
            encoding="utf-8",
        )
        return cache

    def test_force_false_reads_disk_without_network(self):
        self._seed()

        def _boom(*args, **kwargs):
            raise AssertionError("缓存命中时不应发起网络请求")

        with mock.patch.object(trending._SESSION, "get", _boom):
            data = trending.get_star_gainers()
        self.assertEqual(data[0]["repo"], "fake/repo")

    def test_force_true_bypasses_cache_and_overwrites_on_success(self):
        cache = self._seed()
        page = "<html>" + article("real/repo", 500, 42) + "</html>"
        resp = mock.Mock(status_code=200, text=page)
        with mock.patch.object(trending._SESSION, "get", return_value=resp):
            data = trending.get_star_gainers(force=True)
        self.assertEqual(data[0]["repo"], "real/repo")
        disk = json.loads(cache.read_text(encoding="utf-8"))
        self.assertEqual(disk[0]["repo"], "real/repo")  # 成功后覆盖当日缓存

    def test_force_true_failure_keeps_old_cache(self):
        cache = self._seed()
        with mock.patch.object(trending._SESSION, "get", side_effect=OSError("offline")):
            with self.assertRaises(OSError):
                trending.get_star_gainers(force=True)
        self.assertTrue(cache.exists())  # 失败不破坏旧缓存，看板可继续展示上次数据


if __name__ == "__main__":
    unittest.main()
