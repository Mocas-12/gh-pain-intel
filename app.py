"""Streamlit 看板：gh-pain-intel 交互式前端。

运行：streamlit run app.py
"""
from __future__ import annotations

import os
import sys
import threading
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import streamlit as st

from src.ai_engine import DEFAULT_BASE_URL, DEFAULT_MODEL, PainIntelEngine
from src.report import SEVERITY_ORDER, build_report, pct_str
from src.scraper import GitHubRateLimitError, GitHubClient, fetch_many

st.set_page_config(page_title="gh-pain-intel · 开源痛点情报看板", page_icon="🛰️", layout="wide")

st.title("🛰️ gh-pain-intel · 开源社区痛点情报看板")
st.caption(
    "监控指定仓库近一周 Issue → Ox Alpha 语义聚类与情绪研判 → 一键导出 Markdown 市场研究报告"
    "（只读分析，仅供内部研究）"
)


def _get_secret(key: str, default: str = "") -> str:
    """读取密钥：优先 Streamlit Cloud Secrets，其次环境变量（本地 .env 由引擎自动加载）。"""
    try:
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.environ.get(key, default)


# ---------------- 侧边栏配置 ----------------
with st.sidebar:
    st.header("⚙️ 配置")
    repos_raw = st.text_area(
        "目标仓库（每行一个 owner/repo）",
        "ollama/ollama\nlangchain-ai/langchain",
        height=110,
    )
    days = st.slider("时间窗口（天）", 1, 30, 7)
    max_per_repo = st.slider("每个仓库最大 Issue 数", 20, 500, 120, step=20)
    include_comments = st.checkbox("抓取热门评论作为上下文", value=True)
    github_token = st.text_input(
        "GitHub Token（可选，提升 API 限额）",
        type="password",
        value=_get_secret("GITHUB_TOKEN"),
        help="云端部署强烈建议配置：Streamlit 共享出口 IP 的匿名配额（60次/时）极易耗尽；配置后提升至 5000 次/小时",
    )
    with st.expander("🧠 模型设置（OpenRouter · Ox Alpha）"):
        st.caption(f"🔒 固定端点：{DEFAULT_BASE_URL}（本项目强制使用 OpenRouter）")
        model = st.text_input("模型名称", DEFAULT_MODEL)
        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            value=_get_secret("OPENROUTER_API_KEY"),
            placeholder="sk-or-v1-…（云端可在 App Settings → Secrets 中配置）",
        )
        temperature = st.slider("Temperature", 0.0, 1.0, 0.2)
        col_b, col_w = st.columns(2)
        batch_size = col_b.slider("批大小（条/请求）", 5, 30, 10)
        max_workers = col_w.slider("并发请求数", 1, 8, 4)
        st.caption("⚡ 并发批处理可大幅提升分类速度；但并发过高会触发平台限流(429)，退避重试反而变慢")

run_btn = st.button("🚀 开始抓取与分析", type="primary", use_container_width=True)

# ---------------- 会话状态 ----------------
for key in ("result", "scrape_meta", "errors"):
    st.session_state.setdefault(key, None)

if run_btn:
    repos = [r.strip() for r in repos_raw.splitlines() if "/" in r.strip()]
    if not repos:
        st.error("请至少填写一个 owner/repo 格式的仓库")
        st.stop()
    if not (api_key or "").strip():
        st.error("请先在侧边栏填写 OpenRouter API Key（或设置环境变量 OPENROUTER_API_KEY）。")
        st.stop()

    progress = st.progress(0.0, text="准备中…")
    status = st.empty()

    client = GitHubClient(token=github_token or None)

    # 配额可视化（/rate_limit 端点本身不消耗配额）
    quota = client.rate_limit()
    if quota:
        tag = "Token 认证" if quota["authenticated"] else "匿名共享 IP"
        reset_txt = (
            f" · 重置于 {datetime.fromtimestamp(quota['reset'], tz=timezone.utc).astimezone():%H:%M}"
            if quota["remaining"] < quota["limit"]
            else ""
        )
        st.caption(f"📦 GitHub 配额（{tag}）：{quota['remaining']}/{quota['limit']}{reset_txt}")
        if not quota["authenticated"] and quota["remaining"] < max_per_repo:
            st.warning("⚠️ 匿名配额偏低。云端部署请在 Secrets 中配置 GITHUB_TOKEN（5000 次/小时）。")

    try:
        issues, errors = fetch_many(
            client,
            repos,
            days=days,
            max_per_repo=max_per_repo,
            include_comments=include_comments,
            progress_cb=status.write,
        )
    except GitHubRateLimitError as exc:
        progress.empty()
        st.error(f"🚫 {exc}")
        st.info(
            "💡 解决方法：应用右下角 **Manage app → Settings → Secrets** 添加：\n\n"
            '```toml\nGITHUB_TOKEN = "ghp_你的PersonalAccessToken"\n```\n\n'
            "PAT 生成地址：https://github.com/settings/tokens（无需勾选任何权限，public repo 只读即可）"
        )
        st.stop()
    if not issues:
        st.error("未能抓取到任何 Issue：" + "; ".join(errors))
        st.stop()

    progress.progress(0.25, text=f"已抓取 {len(issues)} 条 Issue，正在连接 OpenRouter…")
    engine = PainIntelEngine(
        DEFAULT_BASE_URL, model, api_key.strip(), temperature, max_workers=max_workers
    )
    if not engine.health_check():
        st.error(
            f"无法连接 OpenRouter（{DEFAULT_BASE_URL}）或 API Key 无效。"
            f"请检查网络与 Key（管理地址：https://openrouter.ai/keys）。"
        )
        st.stop()

    stage_names = {
        "classify": "逐条分类与情绪标注",
        "cluster": "语义聚类提炼主题",
        "trends": "趋势与情绪研判",
    }

    # ---------- 后台线程执行分析，主线程每秒心跳刷新进度 ----------
    state = {"stage": "classify", "ratio": 0.0, "error": None, "result": None, "done": False}

    def stage_progress(stage: str, ratio: float) -> None:
        state["stage"], state["ratio"] = stage, ratio

    def worker() -> None:
        try:
            state["result"] = engine.run_pipeline(
                issues, batch_size=batch_size, max_workers=max_workers, progress_cb=stage_progress
            )
        except Exception as exc:
            state["error"] = exc
        finally:
            state["done"] = True

    t = threading.Thread(target=worker, daemon=True)
    t0 = time.time()
    t.start()
    while not state["done"]:
        t.join(timeout=1.0)
        elapsed = time.time() - t0
        ratio = state["ratio"]
        progress.progress(
            min(0.25 + 0.74 * ratio, 0.999),
            text=f"{stage_names[state['stage']]}… ({ratio:.0%}) · 已耗时 {elapsed:.0f} 秒"
            f"（深度推理模型单批约 1-3 分钟，请耐心等待）",
        )
    progress.progress(1.0, text="✅ 分析完成")

    if state["error"] is not None:
        st.error(f"分析失败：{state['error']}")
        st.stop()
    result = state["result"]

    if engine.last_failures:
        st.warning(
            f"⚠️ {len(engine.last_failures)} 个批次分类失败，已用默认值兜底（不影响其余样本）："
            + "; ".join(engine.last_failures[:3])
        )
    st.session_state.result = result
    st.session_state.errors = errors
    st.session_state.scrape_meta = {
        "repos": repos,
        "days": days,
        "total": len(issues),
        "model": model,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    progress.progress(1.0, text="✅ 分析完成")

# ---------------- 结果展示 ----------------
if st.session_state.result:
    result = st.session_state.result
    meta = st.session_state.scrape_meta
    classified = result["classified"]
    themes = result["themes"]
    trends = result["trends"]

    if st.session_state.errors:
        st.warning("部分仓库抓取失败：" + "; ".join(st.session_state.errors))

    bugs = sum(1 for c in classified if c["category"] == "bug")
    feats = sum(1 for c in classified if c["category"] == "feature")
    neg = sum(1 for c in classified if c["emotion"] in ("negative", "angry"))
    total = len(classified)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📦 分析样本", total)
    m2.metric("🐞 缺陷占比", pct_str(bugs, total))
    m3.metric("🚀 功能诉求占比", pct_str(feats, total))
    m4.metric("😠 负面情绪", pct_str(neg, total))
    m5.metric("🧭 整体情绪", trends.get("overall_sentiment", "N/A"))

    tab_pain, tab_feat, tab_trend, tab_report = st.tabs(
        ["🐞 高频痛点", "🚀 功能诉求", "📈 情绪与趋势", "📄 研究报告"]
    )

    # ----- 板块一 -----
    with tab_pain:
        pain_themes = sorted(
            [t for t in themes if t["category"] == "bug"],
            key=lambda t: (SEVERITY_ORDER.get(str(t["severity"]), 1), -t["frequency"]),
        )
        for t in pain_themes:
            with st.container(border=True):
                cols = st.columns([4, 1, 1])
                cols[0].markdown(f"### {t['name']}")
                cols[1].metric("频次", t["frequency"])
                cols[2].metric("严重度", t["severity"])
                st.markdown(f"> {t['insight']}")
                for q in t["representatives"]:
                    st.caption(f"💬 {q}")
        st.divider()
        st.subheader("痛感最高的 Issue")
        top = sorted(classified, key=lambda c: (-c["pain_level"], -(c["issue"].comments_count)))[:10]
        df = pd.DataFrame(
            [
                {
                    "仓库": c["issue"].repo,
                    "编号": f"#{c['issue'].number}",
                    "痛点概括": c["summary"],
                    "痛感": c["pain_level"],
                    "情绪": c["emotion"],
                    "链接": c["issue"].url,
                }
                for c in top
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ----- 板块二 -----
    with tab_feat:
        feat_themes = sorted(
            [t for t in themes if t["category"] == "feature"], key=lambda t: -t["frequency"]
        )
        for t in feat_themes:
            with st.container(border=True):
                cols = st.columns([4, 1, 1])
                cols[0].markdown(f"### {t['name']}")
                cols[1].metric("呼声", t["frequency"])
                cols[2].metric("紧迫度", t["severity"])
                st.markdown(f"> {t['insight']}")
                for q in t["representatives"]:
                    st.caption(f"💬 {q}")
        if trends.get("opportunities"):
            st.info("**🎯 产品机会点**：" + "；".join(trends["opportunities"]))

    # ----- 板块三 -----
    with tab_trend:
        emo_order = ["positive", "neutral", "negative", "angry"]
        emo_zh = {"positive": "😊 正面", "neutral": "😐 中性", "negative": "🙁 负面", "angry": "😠 愤怒"}
        emo_df = pd.DataFrame(
            {
                "情绪": [emo_zh[k] for k in emo_order],
                "条数": [sum(1 for c in classified if c["emotion"] == k) for k in emo_order],
            }
        ).set_index("情绪")
        st.bar_chart(emo_df)
        if trends.get("hot_topics"):
            st.markdown("**🔥 热度上升话题**：" + "；".join(trends["hot_topics"]))
        if trends.get("risks"):
            st.warning("**⚠️ 风险信号**：" + "；".join(trends["risks"]))
        st.success(f"**趋势研判**：{trends.get('trend_summary', 'N/A')}")

    # ----- 报告 -----
    with tab_report:
        md = build_report(meta, result)
        fname = "pain-intel-" + meta["generated_at"].replace(":", "").replace(" ", "_") + ".md"
        st.download_button(
            "⬇️ 一键下载 Markdown 研究报告",
            md,
            file_name=fname,
            mime="text/markdown",
            use_container_width=True,
        )
        st.divider()
        st.markdown(md)
else:
    st.info("👈 在侧边栏配置仓库与模型后，点击「开始抓取与分析」生成情报看板。")
