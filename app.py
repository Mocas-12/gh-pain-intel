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
import plotly.express as px
import streamlit as st

from src.ai_engine import PainIntelEngine
from src.llm_providers import DEFAULT_PROVIDER, PROVIDERS
from src.report import SEVERITY_ORDER, build_report, pct_str
from src.scraper import GitHubRateLimitError, GitHubClient, fetch_many
from src.trending import get_star_gainers
from src.ui import gain_card, hero, inject, section_head, stat_cards, theme_card

st.set_page_config(page_title="GH-PAIN-INTEL · 痛点情报中心", page_icon="🛰️", layout="wide")
inject()

hero(
    "LIVE INTEL · OX ALPHA",
    "开源社区痛点情报中心",
    "GitHub Issue 监控 → 多模型深度语义分析 → 一键导出市场研究报告（只读 · 内部研究用途）",
)


def _add_repo(repo: str) -> None:
    """把仓库追加到侧边栏目标列表（去重）。"""
    lines = [x.strip() for x in st.session_state.get("repos_box", "").splitlines() if x.strip()]
    if repo not in lines:
        lines.append(repo)
    st.session_state.repos_box = "\n".join(lines)


# ---------------- 每日 Star 增幅榜（主页顶部 · 每日更新） ----------------
try:

    @st.cache_data(ttl=21600, show_spinner=False)
    def _load_hot():
        return get_star_gainers()

    hot_repos = _load_hot()
except Exception as exc:
    st.caption(f"⚠️ 榜单暂时不可用：{exc}")
    hot_repos = []

section_head(
    "🔥 今日 STAR 增幅 TOP 10",
    "GitHub 官方 Trending · 最近一天新增星标 · 每日更新",
)

if hot_repos:
    for start in range(0, len(hot_repos), 2):  # 两列卡片栅格，按名次左右、自上而下排列
        pair = hot_repos[start : start + 2]
        cells = st.columns(2, gap="small")
        for cell, (rank, r) in zip(cells, enumerate(pair, start=start + 1)):
            info, add = cell.columns([14, 1], vertical_alignment="center")
            info.markdown(gain_card(r, rank), unsafe_allow_html=True)
            add.button(
                "➕",
                key=f"add_{r['repo']}",
                on_click=_add_repo,
                args=(r["repo"],),
                help=f"添加 {r['repo']} 到目标列表",
                use_container_width=True,
            )
else:
    st.info("榜单暂无数据：数据源为 GitHub 官方 Trending 页面，稍后刷新页面重试")

st.divider()


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
        key="repos_box",
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
    with st.expander("🧠 模型设置（多服务商可切换）"):

        def _sync_provider() -> None:
            """切换服务商时，自动带出该服务商的官方端点与默认模型。"""
            p = PROVIDERS[st.session_state["llm_provider"]]
            st.session_state["llm_base_url"] = p["base_url"]
            if p["models"]:
                st.session_state["llm_model"] = p["models"][0]

        provider_id = st.selectbox(
            "服务商",
            list(PROVIDERS),
            format_func=lambda k: PROVIDERS[k]["label"],
            key="llm_provider",
            on_change=_sync_provider,
        )
        preset = PROVIDERS[provider_id]

        base_url = st.text_input(
            "API 端点（OpenAI 兼容）",
            value=preset["base_url"],
            key="llm_base_url",
            help="分析层兼容 OpenAI Chat Completions 协议；切换服务商自动带出官方端点，也可手动修改",
        )

        if preset["models"]:
            model_choice = st.selectbox(
                "模型", preset["models"] + ["✏️ 其他（手动输入）"], key="llm_model"
            )
            model = (
                st.text_input("自定义模型名称", key="llm_model_custom")
                if model_choice == "✏️ 其他（手动输入）"
                else model_choice
            )
        else:
            model = st.text_input("模型名称", key="llm_model_custom")

        if preset["key_env"] is None:  # 目前仅本地 Ollama 免鉴权
            api_key = "ollama"  # 占位 Bearer，引擎要求非空
            st.caption("🏠 当前服务商无需 API Key")
        else:
            key_help = (
                f"获取地址：{preset['key_url']}；云端可在 Secrets 配置 {preset['key_env']}，选中该服务商后自动带入"
                if preset["key_url"]
                else "可选，仅当你的端点需要鉴权时填写"
            )
            api_key = st.text_input(
                f"{preset['short']} API Key",
                type="password",
                value=_get_secret(preset["key_env"]),
                placeholder=preset["key_hint"] or "选填",
                help=key_help,
            )

        if preset.get("note"):
            st.caption(f"ℹ️ {preset['note']}")

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
    if not base_url.strip():
        st.error("请先在侧边栏填写 API 端点（base_url）")
        st.stop()
    if not (model or "").strip():
        st.error("请先在侧边栏选择或填写模型名称")
        st.stop()
    if not (api_key or "").strip():
        if provider_id == "custom":
            api_key = "none"  # 免鉴权端点的占位 Bearer；需鉴权的端点会收到 401 并提示
        else:
            st.error("请先在侧边栏填写当前服务商的 API Key（或设置对应环境变量）。")
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

    progress.progress(0.25, text=f"已抓取 {len(issues)} 条 Issue，正在连接模型端点…")
    engine = PainIntelEngine(
        base_url.strip(), model.strip(), api_key.strip(), temperature, max_workers=max_workers
    )
    if not engine.health_check():
        st.error(
            f"无法连接模型端点（{base_url}）或 API Key / 模型名无效。"
            f"请检查网络与配置（Key 管理：{preset['key_url'] or '服务商控制台'}）。"
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

    stat_cards(
        [
            ("分析样本", f"{total}<small> 条</small>", "#22d3ee"),
            ("缺陷占比", pct_str(bugs, total), "#f87171"),
            ("功能诉求", pct_str(feats, total), "#34d399"),
            ("负面情绪", pct_str(neg, total), "#fbbf24"),
            ("整体情绪", trends.get("overall_sentiment", "N/A"), "#8b5cf6"),
        ]
    )

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
            st.markdown(theme_card(t), unsafe_allow_html=True)
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
            st.markdown(theme_card(t), unsafe_allow_html=True)
        if trends.get("opportunities"):
            st.info("**🎯 产品机会点**：" + "；".join(trends["opportunities"]))

    # ----- 板块三 -----
    with tab_trend:
        emo_order = ["positive", "neutral", "negative", "angry"]
        emo_zh = {"positive": "😊 正面", "neutral": "😐 中性", "negative": "🙁 负面", "angry": "😠 愤怒"}
        emo_counts = [sum(1 for c in classified if c["emotion"] == k) for k in emo_order]
        emo_colors = {
            "positive": "#34d399",
            "neutral": "#64748b",
            "negative": "#fbbf24",
            "angry": "#f87171",
        }
        fig = px.bar(
            x=[emo_zh[k] for k in emo_order],
            y=emo_counts,
            color=[emo_zh[k] for k in emo_order],
            color_discrete_map={emo_zh[k]: emo_colors[k] for k in emo_order},
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            height=340,
            margin=dict(l=10, r=10, t=24, b=10),
            yaxis_title=None,
            xaxis_title=None,
        )
        fig.update_xaxes(gridcolor="rgba(148,163,184,.12)")
        fig.update_yaxes(gridcolor="rgba(148,163,184,.12)")
        st.plotly_chart(fig, use_container_width=True)
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
    hero("STANDBY", "等待情报采集指令", "在侧边栏完成配置后，点击「开始抓取与分析」启动分析管线")
    current_provider = PROVIDERS.get(
        st.session_state.get("llm_provider", DEFAULT_PROVIDER), {}
    ).get("short", "Ox Alpha")
    stat_cards(
        [
            ("系统状态", "待命", "#22d3ee"),
            ("数据源", "GitHub API", "#8b5cf6"),
            ("分析引擎", current_provider, "#34d399"),
        ]
    )
