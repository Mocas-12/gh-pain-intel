"""命令行批处理入口（适合定时任务/无人值守）。

示例：
    python cli.py --repos ollama/ollama,vllm-project/vllm --days 7 --out report.md
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai_engine import DEFAULT_BASE_URL, DEFAULT_MODEL, PainIntelEngine
from src.report import build_report
from src.scraper import GitHubClient, fetch_many


def main() -> None:
    ap = argparse.ArgumentParser(description="开源社区痛点情报批量分析")
    ap.add_argument("--repos", required=True, help="逗号分隔的 owner/repo 列表")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--max-per-repo", type=int, default=120)
    ap.add_argument("--no-comments", action="store_true", help="不抓取评论上下文")
    ap.add_argument("--base-url", default=os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL))
    ap.add_argument("--model", default=os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL))
    ap.add_argument("--api-key", default=os.environ.get("OPENROUTER_API_KEY"))
    ap.add_argument("--out", default="pain_intel_report.md")
    args = ap.parse_args()

    if not args.api_key:
        sys.exit("缺少 OpenRouter API Key：请设置环境变量 OPENROUTER_API_KEY 或用 --api-key 传入。")

    repos = [r.strip() for r in args.repos.split(",") if r.strip()]

    print(f"[1/3] 抓取 {repos} 近 {args.days} 天的 Issues …")
    client = GitHubClient(token=os.environ.get("GITHUB_TOKEN"))
    issues, errors = fetch_many(
        client,
        repos,
        days=args.days,
        max_per_repo=args.max_per_repo,
        include_comments=not args.no_comments,
        progress_cb=print,
    )
    if errors:
        print("[警告] 部分仓库失败：")
        for e in errors:
            print("  -", e)
    if not issues:
        sys.exit("未抓取到任何 Issue，退出。")

    print(f"[2/3] 共 {len(issues)} 条样本，调用模型 {args.model} @ {args.base_url} …")
    engine = PainIntelEngine(args.base_url, args.model, args.api_key)
    result = engine.run_pipeline(issues, progress_cb=lambda s, r: print(f"  {s}: {r:.0%}"))

    meta = {
        "repos": repos,
        "days": args.days,
        "total": len(issues),
        "model": args.model,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    md = build_report(meta, result)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[3/3] ✅ 报告已写入 {args.out}")


if __name__ == "__main__":
    main()
