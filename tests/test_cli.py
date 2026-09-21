"""CLI 入口冒烟测试：参数解析与快速失败路径（不打网络）。"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

CLI_PATH = Path(__file__).resolve().parent.parent / "cli.py"


class CliSmokeTest(unittest.TestCase):
    def test_help_lists_flags_and_exits_zero(self):
        proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "--help"],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 0)
        for flag in ("--repos", "--days", "--provider", "--out-dir"):
            self.assertIn(flag, proc.stdout)

    def test_missing_required_arg_fails_fast(self):
        proc = subprocess.run(
            [sys.executable, str(CLI_PATH)],
            capture_output=True, text=True, timeout=60,
        )
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
