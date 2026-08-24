"""离线冒烟测试：不依赖网络与本地模型。

运行：python -m unittest discover -s tests -v
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai_engine import _extract_json
from src.report import build_report
from src.scraper import Issue


def fake_result():
    issues = [
        Issue("demo/demo", 1, "crash on start", "app crashes immediately", "open", ["bug"], 12, 30,
              "2026-08-20", "2026-08-21", "http://x/1"),
        Issue("demo/demo", 2, "please add dark mode", "would love a dark theme", "open", ["enhancement"],
              5, 8, "2026-08-19", "2026-08-22", "http://x/2"),
    ]
    classified = [
        {"issue": issues[0], "category": "bug", "pain_level": 5, "emotion": "angry",
         "summary": "启动即崩溃"},
        {"issue": issues[1], "category": "feature", "pain_level": 2, "emotion": "neutral",
         "summary": "希望支持暗色模式"},
    ]
    themes = [
        {"name": "启动崩溃", "category": "bug", "frequency": 1, "severity": "高",
         "representatives": ["crash on start"], "insight": "核心流程稳定性受损"},
        {"name": "暗色模式", "category": "feature", "frequency": 1, "severity": "低",
         "representatives": ["please add dark mode"], "insight": "UI 定制诉求明显"},
    ]
    trends = {
        "overall_sentiment": "中性",
        "sentiment_reason": "测试数据",
        "hot_topics": ["性能"],
        "risks": ["稳定性"],
        "opportunities": ["暗色模式"],
        "trend_summary": "总体平稳。",
    }
    return {"classified": classified, "themes": themes, "trends": trends}


class ExtractJsonTest(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(_extract_json('[{"a":1}]'), [{"a": 1}])

    def test_fenced(self):
        self.assertEqual(_extract_json('```json\n{"ok": true}\n```'), {"ok": True})

    def test_chatty_prefix_suffix(self):
        self.assertEqual(_extract_json('好的，结果如下：\n[1,2]\n以上。'), [1, 2])


class IssueTextTest(unittest.TestCase):
    def test_flat_text_contains_title(self):
        iss = Issue("o/r", 7, "boom", "body", "open", ["bug"], 3, 9, "", "", "u")
        self.assertIn("boom", iss.flat_text)
        self.assertIn("labels: bug", iss.flat_text)


class ReportTest(unittest.TestCase):
    def test_report_sections_present(self):
        md = build_report(
            {"generated_at": "2026-08-24 12:00", "days": 7, "model": "test-model"}, fake_result()
        )
        for sec in ("执行摘要", "高频 Bug 与技术痛点", "功能缺失诉求",
                    "开发者情绪与市场趋势", "附录", "启动崩溃", "暗色模式"):
            self.assertIn(sec, md)

    def test_report_percentages_computed(self):
        md = build_report({"days": 7, "model": "m"}, fake_result())
        self.assertIn("50%", md)  # 1/2 bug, 1/2 feature


class ConcurrentClassifyTest(unittest.TestCase):
    """离线验证并发分类：真并发提速、结果有序、失败兜底。"""

    @staticmethod
    def _fake_ok(payload_delay: float = 0.3):
        import re
        import time as _time

        def fake(system, user, retries=2):
            # 用全局 Issue 编号生成可区分摘要（局部 id 在单条批次中恒为 0）
            nums = [int(x) for x in re.findall(r"\[o/r#(\d+)\]", user)]
            _time.sleep(payload_delay)  # 模拟模型延迟
            return [
                {"id": nums.index(n), "category": "bug", "pain_level": 4,
                 "emotion": "negative", "summary": f"s{n}"}
                for n in nums
            ]
        return fake

    def _engine_with_fake(self, fake_chat_json):
        from src.ai_engine import PainIntelEngine
        eng = PainIntelEngine(api_key="test-key")
        eng.chat_json = fake_chat_json
        return eng

    def _issues(self, n: int):
        return [Issue("o/r", i, f"t{i}", "b", "open", [], 1, 0, "", "", "u") for i in range(n)]

    def test_concurrent_speedup_and_order(self):
        import time
        eng = self._engine_with_fake(self._fake_ok(0.3))
        issues = self._issues(5)
        t0 = time.perf_counter()
        out = eng.classify_issues(issues, batch_size=1, max_workers=5)
        dt = time.perf_counter() - t0
        self.assertEqual(len(out), 5)
        # 顺序与输入一致（summary 序号对应输入顺序）
        self.assertEqual([r["summary"] for r in out], [f"s{i}" for i in range(5)])
        # 串行需 >=1.5s，5 并发应远小于该值
        self.assertLess(dt, 1.2, f"并发未生效，耗时 {dt:.2f}s")

    def test_fallback_on_batch_failure(self):
        def failing(system, user, retries=2):
            raise RuntimeError("boom")
        eng = self._engine_with_fake(failing)
        issues = self._issues(4)
        out = eng.classify_issues(issues, batch_size=2, max_workers=2)
        self.assertEqual(len(out), 4)                  # 结果与输入等长
        self.assertTrue(all("兜底" in r["summary"] for r in out))
        self.assertEqual(len(eng.last_failures), 2)    # 两个批次都记录了失败

    def test_empty_input(self):
        eng = self._engine_with_fake(self._fake_ok())
        self.assertEqual(eng.classify_issues([]), [])


if __name__ == "__main__":
    unittest.main()
