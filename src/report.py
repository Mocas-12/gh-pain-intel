"""报告生成层：把分析结果装配为结构化的 Markdown 市场研究报告。

纯本地拼装（数字统计全部来自真实计数，LLM 只贡献叙述性内容），确保报告可复核。
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime

CATEGORY_ZH = {
    "bug": "🐞 缺陷",
    "feature": "🚀 功能诉求",
    "question": "❓ 疑问",
    "doc": "📚 文档",
    "other": "🔎 其他",
}
SEVERITY_ORDER = {"高": 0, "中": 1, "低": 2}
EMO_ZH = {"positive": "😊 正面", "neutral": "😐 中性", "negative": "🙁 负面", "angry": "😠 愤怒"}


def pct_str(part: int, whole: int) -> str:
    return f"{part / whole:.0%}" if whole else "0%"


def _theme_table(themes: list[dict]) -> str:
    rows = ["| 主题 | 类别 | 频次 | 严重度 | 洞察 |", "|---|---|---|---|---|"]
    for t in sorted(themes, key=lambda x: (SEVERITY_ORDER.get(str(x["severity"]), 1), -x["frequency"])):
        rows.append(
            f"| **{t['name']}** | {CATEGORY_ZH.get(t['category'], t['category'])} "
            f"| {t['frequency']} | {t['severity']} | {t['insight']} |"
        )
    return "\n".join(rows)


def _quotes_block(themes: list[dict], limit_per_theme: int = 2) -> str:
    out: list[str] = []
    for t in themes:
        if t["representatives"]:
            out.append(f"**{t['name']}**")
            out.extend(f"- 💬 {q}" for q in t["representatives"][:limit_per_theme])
    return "\n".join(out)


def build_report(meta: dict, result: dict) -> str:
    classified = result.get("classified", [])
    themes = result.get("themes", [])
    trends = result.get("trends", {})
    total = len(classified)

    cat_counter = Counter(c["category"] for c in classified)
    emo_counter = Counter(c["emotion"] for c in classified)
    repo_counter = Counter(c["issue"].repo for c in classified)

    pain_themes = [t for t in themes if t["category"] == "bug"]
    feat_themes = [t for t in themes if t["category"] == "feature"]
    other_themes = [t for t in themes if t["category"] not in ("bug", "feature")]

    lines = [
        "# 开源社区痛点情报研究报告",
        "",
        f"> 生成时间：{meta.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M'))} · "
        f"数据窗口：近 {meta.get('days', '?')} 天 · 分析模型：{meta.get('model', 'N/A')} · "
        f"样本量：{total} 条 Issue",
        "",
        "## 一、执行摘要",
        "",
        f"- **整体情绪**：{trends.get('overall_sentiment', 'N/A')} —— {trends.get('sentiment_reason', '')}",
        f"- **缺陷类议题**占 {pct_str(cat_counter.get('bug', 0), total)}；"
        f"**功能诉求**占 {pct_str(cat_counter.get('feature', 0), total)}。",
        f"- **负面/愤怒情绪合计** {pct_str(emo_counter.get('negative', 0) + emo_counter.get('angry', 0), total)}。",
        f"- **趋势速览**：{trends.get('trend_summary', 'N/A')}",
        "",
        "## 二、数据概览",
        "",
        "| 仓库 | 样本数 | 占比 |",
        "|---|---|---|",
    ]
    for repo, n in repo_counter.most_common():
        lines.append(f"| `{repo}` | {n} | {pct_str(n, total)} |")
    dist_line = " · ".join(f"{CATEGORY_ZH.get(k, k)} {v}" for k, v in cat_counter.most_common())
    lines += ["", f"**类别分布**：{dist_line or 'N/A'}", ""]

    # ---------- 板块一 ----------
    lines += ["## 三、板块①：高频 Bug 与技术痛点", ""]
    lines.append(_theme_table(pain_themes) if pain_themes else "_本期未识别出显著的缺陷类主题。_")
    if pain_themes:
        lines += ["", "### 社区原声摘录", "", _quotes_block(pain_themes)]

    # ---------- 板块二 ----------
    lines += ["", "## 四、板块②：功能缺失诉求（Feature Requests）", ""]
    lines.append(_theme_table(feat_themes) if feat_themes else "_本期未识别出明确的功能诉求主题。_")
    opps = trends.get("opportunities") or []
    if opps:
        lines += ["", "**产品机会点（供路线图参考）**", ""]
        lines += [f"- 🎯 {o}" for o in opps]

    # ---------- 板块三 ----------
    lines += [
        "",
        "## 五、板块③：开发者情绪与市场趋势",
        "",
        "| 情绪 | 条数 | 占比 |",
        "|---|---|---|",
    ]
    for k in ("positive", "neutral", "negative", "angry"):
        lines.append(
            f"| {EMO_ZH[k]} | {emo_counter.get(k, 0)} | {pct_str(emo_counter.get(k, 0), total)} |"
        )
    if trends.get("hot_topics"):
        lines += ["", "**🔥 热度上升话题**", ""] + [f"- {h}" for h in trends["hot_topics"]]
    if trends.get("risks"):
        lines += ["", "**⚠️ 社区风险信号**", ""] + [f"- {r}" for r in trends["risks"]]
    lines += ["", f"**趋势研判**：{trends.get('trend_summary', 'N/A')}"]

    if other_themes:
        lines += ["", "## 六、其他值得关注的主题", "", _theme_table(other_themes)]

    # ---------- 附录 ----------
    lines += [
        "",
        "---",
        "## 附录：方法说明",
        "",
        f"- 数据来源：GitHub REST API（只读），仓库：{', '.join(f'`{r}`' for r in repo_counter) or 'N/A'}",
        f"- 采集时间：{meta.get('generated_at', 'N/A')}；窗口：{meta.get('days', '?')} 天；按讨论热度排序取样",
        f"- 分析引擎：{meta.get('model', 'N/A')}（OpenAI 兼容端点）；流程：逐条分类 → 两阶段语义聚类 → 趋势研判",
        "- 本报告由自动化管道生成，仅供内部市场研究使用；所引社区文本版权归原作者所有。",
        "",
    ]
    return "\n".join(lines)
