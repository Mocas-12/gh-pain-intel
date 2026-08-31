"""UI 层：自定义样式组件库（Streamlit HTML/CSS 注入）。

设计语言：深空背景 + 霓虹点缀 + 玻璃拟态卡片 + 等宽数字，营造终端指挥中心质感。
注意：本文件中的 CSS 使用普通字符串拼接（非 f-string），避免花括号转义问题。
"""
from __future__ import annotations

import html as _html

import streamlit as st

ACCENT = {"cyan": "#22d3ee", "violet": "#8b5cf6", "green": "#34d399",
          "red": "#f87171", "amber": "#fbbf24"}

_SEV_CLASS = {"高": "sev-high", "中": "sev-mid", "低": "sev-low"}
_CAT_ICON = {"bug": "🐞", "feature": "🚀", "question": "❓", "doc": "📚", "other": "🔎"}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
  --bg:#0a0e14; --panel:#11161f; --panel2:#151c28;
  --line:rgba(148,163,184,.14); --txt:#e2e8f0; --sub:#8b98ad;
}

/* ---------- 全局 ---------- */
.stApp {
  background:
    radial-gradient(1100px 520px at 85% -8%, rgba(34,211,238,.09), transparent 60%),
    radial-gradient(900px 480px at 8% 108%, rgba(139,92,246,.08), transparent 55%),
    var(--bg);
}
html, body, .stApp, [class*="css"] {
  font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif;
  color: var(--txt);
}
.block-container { padding-top: 1.6rem; max-width: 1400px; }
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"] { background:transparent; }
hr { border-color: var(--line); }

/* ---------- 侧边栏 ---------- */
section[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#0d1522 0%,#0a0e14 100%);
  border-right:1px solid var(--line);
}
section[data-testid="stSidebar"] * { color:var(--txt); }
section[data-testid="stSidebar"] hr { margin:.4rem 0; }

/* ---------- Hero 头部 ---------- */
.hero { padding:.4rem 0 .2rem 0; }
.hero-badge {
  display:inline-flex; align-items:center; gap:.45em;
  font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
  letter-spacing:.22em; color:var(--accent-c,#22d3ee);
  border:1px solid rgba(34,211,238,.35); border-radius:999px;
  padding:.32em .95em; margin-bottom:.7em;
  background:rgba(34,211,238,.06);
  text-shadow:0 0 12px rgba(34,211,238,.5);
}
.hero-dot { width:7px;height:7px;border-radius:50%;background:#34d399;
  box-shadow:0 0 8px #34d399; animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.35} }
.hero h1 {
  font-size:2.15rem; font-weight:900; line-height:1.15; margin:0 0 .3rem 0;
  background:linear-gradient(92deg,#f8fafc 20%,#67e8f9 55%,#a78bfa 90%);
  -webkit-background-clip:text; background-clip:text; color:transparent;
}
.hero-sub { color:var(--sub); font-size:.92rem; letter-spacing:.02em; }

/* ---------- 统计卡 ---------- */
.stat-grid { display:flex; gap:13px; flex-wrap:wrap; margin:.35rem 0 1rem 0; }
.stat-card {
  flex:1 1 160px; min-width:158px; position:relative; overflow:hidden;
  background:linear-gradient(180deg,var(--panel2) 0%,rgba(17,22,31,.55) 100%);
  border:1px solid var(--line); border-radius:14px; padding:15px 17px 13px;
  transition:transform .18s ease, border-color .18s ease;
}
.stat-card:hover { transform:translateY(-2px); border-color:rgba(148,163,184,.3); }
.stat-card::before {
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
  background:var(--ac); box-shadow:0 0 14px var(--ac);
}
.stat-num {
  font-family:'JetBrains Mono',monospace; font-size:26px; font-weight:700;
  color:#f8fafc; letter-spacing:-.01em;
}
.stat-num small { font-size:15px; color:var(--sub); font-weight:500; }
.stat-label {
  margin-top:5px; font-size:10.5px; font-weight:700;
  letter-spacing:.14em; text-transform:uppercase; color:var(--sub);
}

/* ---------- 主题洞察卡 ---------- */
.theme-card {
  background:linear-gradient(180deg,var(--panel2) 0%,rgba(17,22,31,.5) 100%);
  border:1px solid var(--line); border-radius:14px;
  padding:16px 19px; margin-bottom:13px;
}
.theme-head { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.theme-name { font-size:1.06rem; font-weight:700; color:#f1f5f9; }
.badge {
  font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
  padding:.25em .7em; border-radius:999px; border:1px solid;
}
.freq { margin-left:auto; color:var(--sub); font-size:12px;
  font-family:'JetBrains Mono',monospace; }
.sev-high { color:#fca5a5; border-color:rgba(248,113,113,.4); background:rgba(248,113,113,.09); }
.sev-mid  { color:#fcd34d; border-color:rgba(251,191,36,.4);  background:rgba(251,191,36,.09); }
.sev-low  { color:#67e8f9; border-color:rgba(34,211,238,.4);  background:rgba(34,211,238,.09); }
.theme-insight { margin:.65rem 0 .2rem; color:#cbd5e1; font-size:.93rem;
  border-left:2px solid var(--ac,#22d3ee); padding-left:.75em; }
.quote { color:var(--sub); font-size:.84rem; margin-top:.3rem; padding-left:1em; }

/* ---------- Star 增幅榜 ---------- */
.section-head { display:flex; align-items:baseline; gap:14px; flex-wrap:wrap;
  margin:.15rem 0 .6rem; }
.section-title {
  font-size:1.28rem; font-weight:900; letter-spacing:.03em;
  background:linear-gradient(92deg,#fbbf24 0%,#f8fafc 55%,#67e8f9 100%);
  -webkit-background-clip:text; background-clip:text; color:transparent;
}
.section-sub { color:var(--sub); font-size:.78rem; letter-spacing:.06em; }
.gain-card {
  position:relative; overflow:hidden; height:100%;
  background:linear-gradient(180deg,var(--panel2) 0%,rgba(17,22,31,.5) 100%);
  border:1px solid var(--line); border-radius:14px;
  padding:12px 14px 11px 60px;
  transition:transform .18s ease, border-color .18s ease;
}
.gain-card:hover { transform:translateY(-2px); border-color:rgba(148,163,184,.32); }
.gain-card::before {
  content:''; position:absolute; left:0; top:0; bottom:0; width:3px;
  background:var(--rc,#22d3ee); box-shadow:0 0 12px var(--rc,#22d3ee);
}
.gain-rank {
  position:absolute; left:16px; top:50%; transform:translateY(-50%);
  font-family:'JetBrains Mono',monospace; font-size:21px; font-weight:700;
  color:var(--rc,#22d3ee); text-shadow:0 0 14px var(--rc,#22d3ee);
}
.gain-name {
  font-size:1.02rem; font-weight:700; color:#f1f5f9;
  text-decoration:none; word-break:break-all;
}
.gain-name:hover { color:#67e8f9; }
.gain-meta {
  margin-top:4px; font-family:'JetBrains Mono',monospace;
  font-size:12px; color:var(--sub);
}
.gain-meta b { color:#34d399; font-weight:700; font-size:13px; }
.gain-desc {
  margin-top:4px; color:var(--sub); font-size:.84rem;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}

/* ---------- Tab 胶囊化 ---------- */
.stTabs [data-baseweb="tab-list"] { gap:6px; background:transparent; }
.stTabs [data-baseweb="tab"] {
  border:1px solid var(--line); border-radius:999px;
  padding:6px 18px; background:rgba(17,22,31,.6);
  font-weight:600; color:var(--sub);
}
.stTabs [aria-selected="true"] {
  color:#0a0e14 !important; background:linear-gradient(92deg,#67e8f9,#a78bfa);
  border-color:transparent; box-shadow:0 0 18px rgba(103,232,249,.25);
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display:none; }

/* ---------- 输入控件 ---------- */
.stButton > button {
  width:100%; border:none; border-radius:12px; font-weight:700;
  background:linear-gradient(92deg,#0891b2,#7c3aed); color:#fff;
  box-shadow:0 4px 22px rgba(124,58,237,.35);
  transition:filter .15s ease;
}
.stButton > button:hover { filter:brightness(1.15); }
.stDownloadButton > button {
  width:100%; border:1px solid rgba(52,211,153,.45); border-radius:12px;
  background:rgba(52,211,153,.08); color:#6ee7b7; font-weight:700;
}
input, textarea { border-radius:10px !important; }
"""


def inject() -> None:
    """注入全局样式（在 set_page_config 之后调用一次）。"""
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(badge: str, title: str, sub: str) -> None:
    """页面顶部渐变大标题。"""
    esc = lambda s: _html.escape(str(s))
    st.markdown(
        '<div class="hero">'
        f'<div class="hero-badge"><span class="hero-dot"></span>{esc(badge)}</div>'
        f'<h1>{esc(title)}</h1>'
        f'<div class="hero-sub">{esc(sub)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def stat_cards(items: list[tuple[str, str, str]]) -> None:
    """一行发光统计卡。items: [(标签, 数值, 强调色)]。"""
    cells = "".join(
        f'<div class="stat-card" style="--ac:{color}">'
        f'<div class="stat-num">{_html.escape(value)}</div>'
        f'<div class="stat-label">{_html.escape(label)}</div></div>'
        for label, value, color in items
    )
    st.markdown(f'<div class="stat-grid">{cells}</div>', unsafe_allow_html=True)


def section_head(title: str, sub: str = "") -> None:
    """区块标题：渐变大字 + 灰色说明。"""
    sub_html = f'<span class="section-sub">{_html.escape(sub)}</span>' if sub else ""
    st.markdown(
        '<div class="section-head">'
        f'<span class="section-title">{_html.escape(title)}</span>{sub_html}'
        "</div>",
        unsafe_allow_html=True,
    )


def gain_card(item: dict, rank: int) -> str:
    """Star 增幅榜单卡 HTML。rank 1-3 有金银铜强调色，其余为青色。"""
    esc = _html.escape
    rank_color = {1: "#fbbf24", 2: "#e2e8f0", 3: "#fb923c"}.get(rank, "#22d3ee")
    desc = (item.get("description") or "").strip()
    return (
        f'<div class="gain-card" style="--rc:{rank_color}">'
        f'<div class="gain-rank">{rank:02d}</div>'
        f'<a class="gain-name" href="{esc(item.get("url", "#"))}" target="_blank">'
        f'{esc(item.get("repo", "?"))}</a>'
        f'<div class="gain-meta"><b>+{int(item.get("gained", 0)):,}</b> ⭐ 今日'
        f' · 全站 {int(item.get("stars", 0)):,}'
        f' · {esc(item.get("language") or "-")}</div>'
        + (f'<div class="gain-desc">{esc(desc)}</div>' if desc else "")
        + "</div>"
    )


def theme_card(theme: dict) -> str:
    """单个主题洞察卡片的 HTML。"""
    sev = str(theme.get("severity", "中"))
    sev_cls = _SEV_CLASS.get(sev, "sev-mid")
    icon = _CAT_ICON.get(str(theme.get("category", "")), "◆")
    accent = ACCENT["red"] if sev == "高" else ACCENT["amber"] if sev == "中" else ACCENT["cyan"]
    quotes = "".join(
        f'<div class="quote">💬 {_html.escape(q)}</div>'
        for q in theme.get("representatives", [])
    )
    return (
        '<div class="theme-card">'
        '<div class="theme-head">'
        f'<span>{icon}</span>'
        f'<span class="theme-name">{_html.escape(str(theme["name"]))}</span>'
        f'<span class="badge {sev_cls}">{_html.escape(sev)}风险</span>'
        f'<span class="freq">× {theme.get("frequency", "?")} 条相关 Issue</span>'
        "</div>"
        f'<div class="theme-insight" style="--ac:{accent}">{_html.escape(str(theme.get("insight", "")))}</div>'
        + quotes +
        "</div>"
    )
