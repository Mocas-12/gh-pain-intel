"""UI 层：自定义样式组件库（Streamlit HTML/CSS 注入）。

设计语言：深空背景 + 霓虹点缀 + 玻璃拟态卡片 + 等宽数字，营造终端指挥中心质感。
注意：本文件中的 CSS 使用普通字符串拼接（非 f-string），避免花括号转义问题。
"""
from __future__ import annotations

import html as _html

import streamlit as st

ACCENT = {"cyan": "#22d3ee", "red": "#f87171", "amber": "#fbbf24"}

_SEV_CLASS = {"高": "sev-high", "中": "sev-mid", "低": "sev-low"}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=JetBrains+Mono:wght@500;700&family=Noto+Sans+SC:wght@400;500;700;900&display=swap');

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
  font-family:'Inter','Noto Sans SC','Segoe UI',system-ui,-apple-system,sans-serif;
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
  color:#f1f5f9; letter-spacing:.01em;
}
.hero-sub { color:var(--sub); font-size:.92rem; letter-spacing:.02em; }

/* ---------- 统计卡 ---------- */
.stat-grid { display:flex; gap:13px; flex-wrap:wrap; margin:.35rem 0 1rem 0; }
.stat-card {
  flex:1 1 160px; min-width:158px; position:relative; overflow:hidden;
  background:linear-gradient(180deg,var(--panel2) 0%,rgba(17,22,31,.55) 100%);
  border:1px solid var(--line); border-radius:14px; padding:15px 17px 13px;
}
.stat-card::before {
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
  background:var(--ac);
}
.stat-num {
  font-family:'JetBrains Mono',monospace; font-size:26px; font-weight:700;
  color:#f8fafc; letter-spacing:-.01em;
}
.stat-num small { font-size:15px; color:var(--sub); font-weight:500; }
.stat-label {
  margin-top:5px; font-size:10.5px; font-weight:700;
  letter-spacing:.08em; color:var(--sub);
}
.stat-note { margin-top:2px; font-size:11px; color:var(--sub); opacity:.78; }

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
  font-size:1.28rem; font-weight:900; letter-spacing:.02em; color:#f1f5f9;
}
.section-sub { color:var(--sub); font-size:.78rem; letter-spacing:.02em; }
.section-meta { margin-left:auto; font-family:'JetBrains Mono',monospace;
  font-size:11.5px; color:var(--sub); }
.gain-card {
  position:relative; overflow:hidden; height:100%;
  background:linear-gradient(180deg,var(--panel2) 0%,rgba(17,22,31,.5) 100%);
  border:1px solid var(--line); border-radius:14px;
  padding:12px 14px 12px 60px;
}
.gain-card::before {
  content:''; position:absolute; left:0; top:0; bottom:0; width:3px;
  background:var(--rc,#22d3ee);
}
/* 前三名奖牌感：加宽光柱、放大名次数字——全页唯一的发光重点 */
.gain-card.medal::before { width:4px; box-shadow:0 0 12px var(--rc); }
.gain-rank {
  position:absolute; left:16px; top:50%; transform:translateY(-50%);
  font-family:'JetBrains Mono',monospace; font-size:19px; font-weight:700;
  color:var(--rc,#22d3ee);
}
.gain-card.medal .gain-rank { font-size:25px; text-shadow:0 0 14px var(--rc); }
.gain-head { display:flex; align-items:center; gap:8px; min-width:0; }
.gain-name {
  font-size:1.02rem; font-weight:700; color:#f1f5f9;
  text-decoration:none; word-break:break-all;
}
.gain-name:hover { color:#67e8f9; }
.gain-lang {
  flex:none; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:500;
  color:var(--sub); border:1px solid var(--line); border-radius:6px; padding:.12em .5em;
}
.gain-meta {
  margin-top:4px; display:flex; justify-content:space-between; align-items:baseline;
  font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--sub);
}
.gain-meta b { color:#34d399; font-weight:700; font-size:13px; }
.gain-bar { margin-top:6px; height:3px; border-radius:2px;
  background:rgba(148,163,184,.14); overflow:hidden; }
.gain-bar i { display:block; height:100%; background:var(--rc,#22d3ee); border-radius:2px; }
.gain-desc {
  margin-top:6px; color:var(--sub); font-size:.84rem; line-height:1.5;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
}
/* 榜单卡右侧 ➕ 图标按钮：按钮列很窄且带 help tooltip 包装层，
   须压缩内边距并单独着色，否则图标被裁切、只剩默认深色底 */
[data-testid="stHorizontalBlock"]:has(.gain-card) .stButton button {
  min-width:0; padding:4px 5px; font-size:15px; line-height:1;
  border:1px solid rgba(34,211,238,.35); border-radius:10px;
  background:rgba(34,211,238,.08); color:#67e8f9; box-shadow:none;
}
[data-testid="stHorizontalBlock"]:has(.gain-card) .stButton button:hover {
  background:rgba(34,211,238,.18); border-color:rgba(34,211,238,.6);
  box-shadow:0 0 12px rgba(34,211,238,.35);
}
/* 榜单标题右侧刷新按钮：与卡片 ➕ 同款的小方块 ghost 图标钮（收窄内边距、宽度贴内容），
   借 st-key-* 包装类精准命中，覆盖全局渐变大按钮样式 */
.st-key-refresh_hot .stButton button {
  width:auto; min-width:0; min-height:0; padding:4px 11px; font-size:17px; font-weight:700; line-height:1.2;
  border:1px solid rgba(34,211,238,.35); border-radius:10px;
  background:rgba(34,211,238,.08); color:#67e8f9; box-shadow:none;
}
.st-key-refresh_hot .stButton button:hover {
  background:rgba(34,211,238,.18); border-color:rgba(34,211,238,.6);
  box-shadow:0 0 12px rgba(34,211,238,.35);
}

/* ---------- Tab 胶囊化 ---------- */
.stTabs [data-baseweb="tab-list"] { gap:6px; background:transparent; }
.stTabs [data-baseweb="tab"] {
  border:1px solid var(--line); border-radius:999px;
  padding:6px 18px; background:rgba(17,22,31,.6);
  font-weight:600; color:var(--sub);
}
.stTabs [aria-selected="true"] {
  color:#67e8f9 !important; background:rgba(34,211,238,.10);
  border-color:rgba(34,211,238,.55); box-shadow:none;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display:none; }

/* ---------- 空状态引导步骤 ---------- */
.guide-grid { display:flex; gap:13px; flex-wrap:wrap; margin:.35rem 0 1rem; }
.guide-card {
  flex:1 1 220px;
  background:linear-gradient(180deg,var(--panel2) 0%,rgba(17,22,31,.55) 100%);
  border:1px solid var(--line); border-radius:14px; padding:16px 18px;
}
.guide-step { font-family:'JetBrains Mono',monospace; font-size:13px; font-weight:700;
  color:#67e8f9; }
.guide-title { margin-top:6px; font-size:1rem; font-weight:700; color:#f1f5f9; }
.guide-desc { margin-top:4px; color:var(--sub); font-size:.85rem; line-height:1.55; }

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
    def esc(s: object) -> str:
        return _html.escape(str(s))
    st.markdown(
        '<div class="hero">'
        f'<div class="hero-badge"><span class="hero-dot"></span>{esc(badge)}</div>'
        f'<h1>{esc(title)}</h1>'
        f'<div class="hero-sub">{esc(sub)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def stat_cards(items: list[tuple[str, str, str, str]]) -> None:
    """一行发光统计卡。items: [(标签, 数值, 强调色, 补充说明)]，说明可为空串。"""
    cells = "".join(
        f'<div class="stat-card" style="--ac:{color}">'
        f'<div class="stat-num">{_html.escape(value)}</div>'
        f'<div class="stat-label">{_html.escape(label)}</div>'
        + (f'<div class="stat-note">{_html.escape(note)}</div>' if note else "")
        + "</div>"
        for label, value, color, note in items
    )
    st.markdown(f'<div class="stat-grid">{cells}</div>', unsafe_allow_html=True)


def section_head(title: str, sub: str = "", meta: str = "") -> None:
    """区块标题：大字标题 + 灰色说明；meta 右对齐（如更新时间）。"""
    sub_html = f'<span class="section-sub">{_html.escape(sub)}</span>' if sub else ""
    meta_html = f'<span class="section-meta">{_html.escape(meta)}</span>' if meta else ""
    st.markdown(
        '<div class="section-head">'
        f'<span class="section-title">{_html.escape(title)}</span>{sub_html}{meta_html}'
        "</div>",
        unsafe_allow_html=True,
    )


def gain_card(item: dict, rank: int, max_gained: int) -> str:
    """Star 增幅榜单卡 HTML。前三名有金银铜奖牌感，其余为青色；
    gain-bar 以当榜最大增量为基准可视化名次。"""
    esc = _html.escape
    rank_color = {1: "#fbbf24", 2: "#cbd5e1", 3: "#fb923c"}.get(rank, "#22d3ee")
    desc = (item.get("description") or "").strip()
    lang = (item.get("language") or "").strip()
    gained = int(item.get("gained", 0))
    pct = max(4, round(gained / max_gained * 100)) if max_gained > 0 else 0
    return (
        f'<div class="gain-card{" medal" if rank <= 3 else ""}" style="--rc:{rank_color}">'
        f'<div class="gain-rank">{rank:02d}</div>'
        f'<div class="gain-head">'
        f'<a class="gain-name" href="{esc(item.get("url", "#"))}" target="_blank">'
        f'{esc(item.get("repo", "?"))}</a>'
        + (f'<span class="gain-lang">{esc(lang)}</span>' if lang and lang != "-" else "")
        + "</div>"
        f'<div class="gain-meta"><span><b>+{gained:,}</b> ⭐ 今日</span>'
        f'<span>全站 {int(item.get("stars", 0)):,}</span></div>'
        f'<div class="gain-bar"><i style="width:{pct}%"></i></div>'
        + (f'<div class="gain-desc">{esc(desc)}</div>' if desc else "")
        + "</div>"
    )


def guide_steps(steps: list[tuple[str, str]]) -> None:
    """空状态的三步行动指引。steps: [(标题, 说明)]。"""
    cells = "".join(
        '<div class="guide-card">'
        f'<div class="guide-step">{i:02d}</div>'
        f'<div class="guide-title">{_html.escape(title)}</div>'
        f'<div class="guide-desc">{_html.escape(desc)}</div>'
        "</div>"
        for i, (title, desc) in enumerate(steps, start=1)
    )
    st.markdown(f'<div class="guide-grid">{cells}</div>', unsafe_allow_html=True)


def theme_card(theme: dict) -> str:
    """单个主题洞察卡片的 HTML。"""
    sev = str(theme.get("severity", "中"))
    sev_cls = _SEV_CLASS.get(sev, "sev-mid")
    accent = ACCENT["red"] if sev == "高" else ACCENT["amber"] if sev == "中" else ACCENT["cyan"]
    quotes = "".join(
        f'<div class="quote">💬 {_html.escape(q)}</div>'
        for q in theme.get("representatives", [])
    )
    return (
        '<div class="theme-card">'
        '<div class="theme-head">'
        f'<span class="theme-name">{_html.escape(str(theme["name"]))}</span>'
        f'<span class="badge {sev_cls}">{_html.escape(sev)}风险</span>'
        f'<span class="freq">× {theme.get("frequency", "?")} 条相关 Issue</span>'
        "</div>"
        f'<div class="theme-insight" style="--ac:{accent}">{_html.escape(str(theme.get("insight", "")))}</div>'
        + quotes +
        "</div>"
    )
