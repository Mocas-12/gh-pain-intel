"""UI 层：自定义样式组件库（Streamlit HTML/CSS 注入）。

设计语言：深色研究工作台，实体表面、清晰索引与证据层级，蓝色仅强调操作。
所有样式在 theme.css 中统一注入，保留 Streamlit 原生控件与应用状态。
"""
from __future__ import annotations

import html as _html
from pathlib import Path

import streamlit as st

ACCENT = {"cyan": "var(--blue)", "red": "var(--red)", "amber": "var(--orange)"}

_SEV_CLASS = {"高": "sev-high", "中": "sev-mid", "低": "sev-low"}
_CAT_LABEL = {"bug": "缺陷", "feature": "需求", "question": "问题", "doc": "文档", "other": "其他"}

def inject() -> None:
    """注入全局样式（在 set_page_config 之后调用一次）。"""
    css = Path(__file__).with_name("theme.css").read_text(encoding="utf-8")
    st.markdown("<style>\n" + css + "\n</style>", unsafe_allow_html=True)


def intel_hero(items: list[dict], updated_at: object = None) -> None:
    """首页情报焦点：摘要与榜单前列的真实增幅构成轻量信号图。"""
    esc = _html.escape
    values = [max(0, int(item.get("gained", 0))) for item in items[:8]]
    peak = max(values, default=0)

    def compact_value(value: int) -> str:
        if value >= 1000:
            return f"{value / 1000:.1f}".removesuffix(".0") + "k"
        return str(value)

    bars = "".join(
        f'<span class="signal-item"><span class="signal-number">+{compact_value(value)}</span>'
        f'<i title="榜单第{rank}：+{value:,} stars" '
        f'aria-label="榜单第{rank}：+{value:,} stars" '
        f'style="height:{max(4, round(value / peak * 40)) if peak else 4}px;'
        '"></i>'
        f'<small>{rank}</small></span>'
        for rank, value in enumerate(values, start=1)
    )
    top_repo = esc(items[0].get("repo", "暂无榜首数据")) if items else "暂无榜首数据"
    top_url = str(items[0].get("url", "")) if items else ""
    top_description = esc(items[0].get("description", "")) if items else ""
    repo_html = (
        f'<a class="signal-repo" href="{esc(top_url)}" target="_blank" rel="noopener noreferrer">'
        f'{top_repo}</a>'
        if top_url.startswith("https://github.com/")
        else f'<span class="signal-repo">{top_repo}</span>'
    )
    description_html = (
        f'<div class="signal-description">{top_description}</div>' if top_description else ""
    )
    peak_text = f"+{peak:,}" if values else "—"
    update_text = f"更新于 {updated_at:%H:%M}" if updated_at else "GitHub Trending 每日更新"
    st.markdown(
        '<section class="intel-hero">'
        '<div class="intel-copy"><div class="hero"><h1>GitHub 痛点情报</h1>'
        '<div class="hero-sub">从 GitHub Issue 与项目热度中，发现正在升温的需求和问题。</div>'
        '</div>'
        '</div><div class="signal-panel"><div class="signal-top">'
        '<span class="signal-label">今日 Star 增幅榜首</span>'
        f'<span><b class="signal-value">{peak_text}</b><span class="signal-unit">stars</span></span>'
        f'</div><div class="signal-scale"><span>增幅</span><span>最高 {peak_text}</span></div>'
        f'<div class="signal-bars" aria-label="柱体按榜单排名排列，悬停查看 Star 增幅">{bars}</div>'
        f'<div class="signal-feature"><span class="signal-rank">#1</span>'
        f'<div class="signal-feature-copy">{repo_html}'
        f'{description_html}'
        '</div></div>'
        f'<div class="signal-foot"><span>前 {len(values)} 名，按日增 Star 排序</span>'
        f'<span>{esc(update_text)}</span></div>'
        '</div></section>',
        unsafe_allow_html=True,
    )


def home_focus(result: dict | None) -> None:
    """显示最新分析中优先级最高的缺陷主题，或首次分析指引。"""
    esc = _html.escape
    bugs = [t for t in (result or {}).get("themes", []) if t.get("category") == "bug"]
    if bugs:
        theme = min(
            bugs,
            key=lambda t: (
                _SEVERITY_ORDER.get(str(t.get("severity", "中")), 1),
                -int(t.get("frequency", 0)),
            ),
        )
        severity = esc(theme.get("severity", "中"))
        label = f"优先关注：{severity}风险，{int(theme.get('frequency', 0))} 条 Issue"
        name = esc(theme.get("name", "未命名主题"))
        detail = esc(theme.get("insight", ""))
        css = "focus-card"
    elif result:
        label, name = "本次分析", "暂未识别出缺陷类主题"
        detail = "可以查看功能诉求、趋势与情绪板块，了解这批 Issue 的其他信号。"
        css = "focus-card focus-empty"
    else:
        label, name = "等待首次分析", "这里会显示最值得优先关注的社区痛点。"
        detail = "先在左侧配置目标仓库和模型，再点击「开始分析 Issue」。"
        css = "focus-card focus-empty"
    st.markdown(
        f'<div class="{css}"><div class="focus-label">{esc(label)}</div>'
        f'<div><div class="focus-main">{name}</div>'
        f'<div class="focus-detail">{detail}</div></div></div>',
        unsafe_allow_html=True,
    )


_SEVERITY_ORDER = {"高": 0, "中": 1, "低": 2}


def stat_cards(items: list[tuple[str, str, str]]) -> None:
    """一行分析摘要。items: [(标签, 数值, 强调色)]。"""
    cells = "".join(
        f'<div class="stat-card" style="--ac:{color}">'
        f'<div class="stat-num">'
        f'{_html.escape(str(value)).replace("&lt;small&gt;", "<small>").replace("&lt;/small&gt;", "</small>")}'
        f'</div>'
        f'<div class="stat-label">{_html.escape(label)}</div></div>'
        for label, value, color in items
    )
    st.markdown(f'<div class="stat-grid">{cells}</div>', unsafe_allow_html=True)


def section_head(title: str, sub: str = "") -> None:
    """区块标题：大字标题 + 灰色说明。"""
    sub_html = f'<span class="section-sub">{_html.escape(sub)}</span>' if sub else ""
    st.markdown(
        '<div class="section-head">'
        f'<span class="section-title">{_html.escape(title)}</span>{sub_html}'
        "</div>",
        unsafe_allow_html=True,
    )


def gain_card(item: dict, rank: int) -> str:
    """Star 增幅榜单行 HTML。排名采用等宽数字；
    days_on_board=1 标 新上榜，>1 标连续天数，None（冷启动）不标。"""
    esc = _html.escape
    desc = (item.get("description") or "").strip()
    lang = (item.get("language") or "").strip()
    days = item.get("days_on_board")
    if days == 1:
        tag = '<span class="board-tag tag-new">新上榜</span>'
    elif isinstance(days, int) and days > 1:
        tag = f'<span class="board-tag tag-streak">×{days} 天</span>'
    else:
        tag = ""
    topics = [esc(t) for t in (item.get("topics") or [])[:4]]
    chips = "".join(f'<span class="topic-chip">#{t}</span>' for t in topics)
    topic_row = f'<div class="topic-row">{chips}</div>'
    lang_txt = esc(lang) if lang and lang != "-" else "-"
    return (
        f'<div class="gain-card gain-top-{rank}">'
        f'<div class="gain-rank">{rank:02d}</div>'
        '<div class="gain-head">'
        f'<a class="gain-name" href="{esc(item.get("url", "#"))}" target="_blank" '
        f'title="{esc(item.get("repo", "?"))}">{esc(item.get("repo", "?"))}</a>{tag}</div>'
        f'<div class="gain-meta"><span><b>+{int(item.get("gained", 0)):,}</b> 今日</span>'
        f'<span>总计 {int(item.get("stars", 0)):,} stars</span>'
        f'<span>{lang_txt}</span></div>'
        + f'<div class="gain-desc">{esc(desc)}</div>'
        + topic_row
        + "</div>"
    )


def theme_card(theme: dict) -> str:
    """单个主题洞察卡片的 HTML。"""
    sev = str(theme.get("severity", "中"))
    sev_cls = _SEV_CLASS.get(sev, "sev-mid")
    category = _CAT_LABEL.get(str(theme.get("category", "")), "其他")
    accent = ACCENT["red"] if sev == "高" else ACCENT["amber"] if sev == "中" else ACCENT["cyan"]
    quotes = "".join(
        f'<div class="quote">{_html.escape(q)}</div>'
        for q in theme.get("representatives", [])
    )
    return (
        '<div class="theme-card">'
        '<div class="theme-head">'
        f'<span class="section-sub">{category}</span>'
        f'<span class="theme-name">{_html.escape(str(theme["name"]))}</span>'
        f'<span class="badge {sev_cls}">{_html.escape(sev)}风险</span>'
        f'<span class="freq">× {theme.get("frequency", "?")} 条相关 Issue</span>'
        "</div>"
        f'<div class="theme-insight" style="--ac:{accent}">{_html.escape(str(theme.get("insight", "")))}</div>'
        + quotes +
        "</div>"
    )
