"""看板 UI 冒烟测试：用 Streamlit AppTest 无头启动 app.py，覆盖「应用能否启动」。

CI 原本只验证 src 层，UI 层的导入错误（如 app.py 引用了 src.ui 不存在的符号）
曾在线上才会暴露。本文件把这类问题拦在合入前。

设计要点：
- 打补丁的对象是 src.trending.get_star_gainers / last_updated，而非 app 模块——
  app.py 每次脚本执行都会 `from src.trending import ...` 重新绑定，补丁自然生效，
  且完全不需要在 bare mode 导入 app.py（避免触发真实网络抓取）；
- 榜单数据用固定假数据，磁盘缓存层不被触达，测试离线确定性。
"""
from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import streamlit as st
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"

FAKE_HOT = [
    {
        "repo": f"demo/repo-{i}",
        "stars": 1000 * i,
        "gained": 100 * (4 - i),
        "language": "Python",
        "description": f"demo repo {i}",
        "url": f"https://github.com/demo/repo-{i}",
    }
    for i in range(1, 4)
]
FAKE_TS = datetime(2026, 9, 22, 8, 30)


def patched_trending():
    """同时替换榜单数据源与更新时间查询，保证离线且结果确定。"""
    return (
        mock.patch("src.trending.get_star_gainers", return_value=FAKE_HOT),
        mock.patch("src.trending.last_updated", return_value=FAKE_TS),
    )


class DashboardBootTest(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()

    def test_dashboard_boots_and_renders_board(self):
        patch_data, patch_ts = patched_trending()
        with patch_data, patch_ts:
            at = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
        self.assertEqual(at.exception, [])
        markdowns = "\n".join(m.value for m in at.markdown)
        self.assertIn("今日 STAR 增幅 TOP 10", markdowns)
        self.assertIn("demo/repo-1", markdowns)          # 榜单卡片渲染
        self.assertIn("更新于 08:30", markdowns)          # section_head 的 meta 通道
        self.assertEqual(
            len([b for b in at.button if b.key == "refresh_hot"]), 1
        )

    def test_refresh_button_forces_refetch_and_toasts(self):
        patch_data, patch_ts = patched_trending()
        with patch_data as data_mock, patch_ts:
            at = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
            self.assertEqual(at.exception, [])
            at.button(key="refresh_hot").click().run()
            self.assertEqual(at.exception, [])
        # 点击必须绕过两层缓存：force=True 直达数据源
        self.assertTrue(
            any(c.kwargs.get("force") is True for c in data_mock.call_args_list),
            f"刷新未强制重抓，调用记录: {data_mock.call_args_list}",
        )
        self.assertTrue(any("榜单已刷新" in t.value for t in at.toast))


if __name__ == "__main__":
    unittest.main()
