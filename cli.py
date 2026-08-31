"""命令行批处理入口（适合定时任务/无人值守）。

示例：
    python cli.py --repos ollama/ollama,vllm-project/vllm --days 7 --out report.md
    python cli.py --provider gemini --repos ollama/ollama --days 7 --out report.md
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai_engine import PainIntelEngine
from src.llm_providers import DEFAULT_PROVIDER, PROVIDERS
from src.report import build_report
from src.scraper import GitHubRateLimitError, GitHubClient, fetch_many


def main() -> None:
    ap = argparse.ArgumentParser(description="开源社区痛点情报批量分析")
    ap.add_argument("--repos", required=True, help="逗号分隔的 owner/repo 列表")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--max-per-repo", type=int, default=120)
    ap.add_argument("--no-comments", action="store_true", help="不抓取评论上下文")
    ap.add_argument("--batch-size", type=int, default=10, help="每次模型请求包含的 Issue 数")
    ap.add_argument("--max-workers", type=int, default=4, help="分类阶段并发请求数（上限8）")
    ap.add_argument(
        "--provider",
        default=os.environ.get("LLM_PROVIDER", DEFAULT_PROVIDER),
        choices=sorted(PROVIDERS),
        help=f"模型服务商，默认 {DEFAULT_PROVIDER}；可选: {', '.join(sorted(PROVIDERS))}",
    )
    ap.add_argument("--base-url", default=None, help="覆盖服务商预设端点（OpenAI 兼容）")
    ap.add_argument("--model", default=None, help="覆盖服务商预设模型")
    ap.add_argument("--api-key", default=None, help="覆盖服务商预设 Key 环境变量")
    ap.add_argument(
        "--out-dir",
        default=None,
        help="报告输出目录（自动按时间戳命名）；与 --out 二选一，本参数优先",
    )
    ap.add_argument("--out", default="pain_intel_report.md")
    args = ap.parse_args()

    # 解析服务商预设：显式参数 > 服务商专属环境变量 > 通用环境变量 > 预设默认值
    preset = PROVIDERS[args.provider]
    if args.provider == "openrouter":  # 兼容历史环境变量
        env_base = os.environ.get("OPENROUTER_BASE_URL")
        env_model = os.environ.get("OPENROUTER_MODEL")
        env_key = os.environ.get("OPENROUTER_API_KEY")
    else:
        env_base = env_model = None
        env_key = os.environ.get(preset["key_env"]) if preset["key_env"] else None

    base_url = args.base_url or env_base or preset["base_url"]
    model = args.model or env_model or (preset["models"][0] if preset["models"] else "")
    api_key = args.api_key or env_key or os.environ.get("LLM_API_KEY") or ""
    if not api_key and preset["key_env"] is None:
        api_key = "ollama"  # 免鉴权服务商（本地 Ollama）的占位 Bearer
    if args.provider == "custom" and not api_key:
        api_key = "none"  # 免鉴权自定义端点的占位 Bearer

    if not base_url:
        sys.exit("缺少 API 端点：请用 --base-url 传入 OpenAI 兼容的 base_url。")
    if not model:
        sys.exit("缺少模型名：请用 --model 传入。")
    if not api_key:
        sys.exit(
            f"缺少 API Key：请设置环境变量 {preset['key_env']}（或通用 LLM_API_KEY），"
            f"或用 --api-key 传入。获取地址：{preset['key_url']}"
        )

    repos = [r.strip() for r in args.repos.split(",") if r.strip()]

    print(f"[1/3] 抓取 {repos} 近 {args.days} 天的 Issues …")
    client = GitHubClient(token=os.environ.get("GITHUB_TOKEN"))
    try:
        issues, errors = fetch_many(
            client,
            repos,
            days=args.days,
            max_per_repo=args.max_per_repo,
            include_comments=not args.no_comments,
            progress_cb=print,
        )
    except GitHubRateLimitError as exc:
        sys.exit(f"🚫 {exc}")
    if errors:
        print("[警告] 部分仓库失败：")
        for e in errors:
            print("  -", e)
    if not issues:
        sys.exit("未抓取到任何 Issue，退出。")

    print(f"[2/3] 共 {len(issues)} 条样本，调用模型 {model} @ {base_url} …")
    engine = PainIntelEngine(base_url, model, api_key, max_workers=args.max_workers)
    result = engine.run_pipeline(
        issues, batch_size=args.batch_size, max_workers=args.max_workers,
        progress_cb=lambda s, r: print(f"  {s}: {r:.0%}"),
    )

    meta = {
        "repos": repos,
        "days": args.days,
        "total": len(issues),
        "model": model,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    md = build_report(meta, result)
    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)
        out_path = os.path.join(
            args.out_dir, f"pain_intel_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        )
    else:
        out_path = args.out or "pain_intel_report.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[3/3] ✅ 报告已写入 {out_path}")


if __name__ == "__main__":
    main()
