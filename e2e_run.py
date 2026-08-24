"""端到端真实验证：GitHub API 抓取 + OpenRouter(Ox Alpha) 完整分析管线。

用法：
    export OPENROUTER_API_KEY=sk-or-v1-xxx
    python e2e_run.py            # 默认 pandas-dev/pandas 近7天6条
可调环境变量：E2E_REPOS（逗号分隔）、E2E_DAYS、E2E_MAX
"""
from __future__ import annotations

import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai_engine import PainIntelEngine
from src.report import build_report
from src.scraper import GitHubClient


def main() -> None:
    t0 = time.time()
    repos = os.environ.get("E2E_REPOS", "pandas-dev/pandas").split(",")
    days = int(os.environ.get("E2E_DAYS", "7"))
    n = int(os.environ.get("E2E_MAX", "6"))

    client = GitHubClient(token=os.environ.get("GITHUB_TOKEN"))
    issues: list = []
    errors: list[str] = []
    for r in repos:
        try:
            issues.extend(
                client.fetch_repo_issues(r.strip(), days=days, max_issues=n, include_comments=False)
            )
        except Exception as exc:
            errors.append(f"{r}: {exc}")
    print(f"[1/2] 抓取 {len(issues)} 条 Issue（耗时 {time.time() - t0:.0f}s）")
    if errors:
        print("  抓取警告:", errors)
    if not issues:
        sys.exit("无样本，终止")

    engine = PainIntelEngine()
    print(f"[2/2] 模型管线: {engine.model} @ {engine.base_url}")
    result = engine.run_pipeline(
        issues, progress_cb=lambda s, r: print(f"   {s} {r:.0%} ({time.time() - t0:.0f}s)")
    )

    cats = Counter(c["category"] for c in result["classified"])
    emos = Counter(c["emotion"] for c in result["classified"])
    print("\n=== 分类统计 ===\n类别:", dict(cats), "\n情绪:", dict(emos))

    print("\n=== 主题簇 ===")
    for t in result["themes"]:
        print(f"  [{t['category']}|{t['severity']}|x{t['frequency']}] {t['name']}: {t['insight'][:60]}")

    tr = result["trends"]
    print("\n=== 趋势研判 ===")
    print("整体情绪:", tr.get("overall_sentiment"), "|", str(tr.get("sentiment_reason", ""))[:80])
    print("机会点:", tr.get("opportunities"))

    meta = {
        "repos": repos,
        "days": days,
        "total": len(issues),
        "model": engine.model,
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
    }
    md = build_report(meta, result)
    with open("e2e_report.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\n✅ 端到端完成：报告已写入 e2e_report.md（{len(md)} 字符，总耗时 {time.time() - t0:.0f}s）")


if __name__ == "__main__":
    main()
