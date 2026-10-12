"""UI 层：自定义样式组件库（Streamlit HTML/CSS 注入）。

设计语言：Apple 深色玻璃——中性近黑背景 + 白色磨砂玻璃卡片（backdrop-blur）+
发丝级描边 + iOS 系统色点缀 + 分段控件 Tab + 系统字体栈。无霓虹、无渐变字、
无发光阴影；交互反馈只用玻璃亮度与轻位移。
注意：本文件中的 CSS 使用普通字符串拼接（非 f-string），避免花括号转义问题。
"""
from __future__ import annotations

import html as _html

import streamlit as st

ACCENT = {"cyan": "#0a84ff", "red": "#ff453a", "amber": "#ff9f0a"}

_SEV_CLASS = {"高": "sev-high", "中": "sev-mid", "低": "sev-low"}
_CAT_ICON = {"bug": "🐞", "feature": "🚀", "question": "❓", "doc": "📚", "other": "🔎"}

# GitHub linguist 语言主色（常见语言；未知语言回退中性灰）
LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Rust": "#dea584", "Go": "#00ADD8", "C": "#555555", "C++": "#f34b7d",
    "C#": "#178600", "Java": "#b07219", "HTML": "#e34c26", "CSS": "#563d7c",
    "Jupyter Notebook": "#DA5B0B", "Shell": "#89e051", "Ruby": "#701516",
    "Vue": "#41b883", "Swift": "#F05138", "Kotlin": "#A97BFF", "PHP": "#4F5D95",
    "Lua": "#000080", "Zig": "#ec915c", "Assembly": "#6E4C13",
}

_CSS = """
<style>
:root {
  --bg:#0e0e11; --panel:rgba(255,255,255,.055); --panel-strong:rgba(255,255,255,.085);
  --line:rgba(255,255,255,.09); --line-strong:rgba(255,255,255,.14);
  --txt:#f5f5f7; --sub:#a1a1a6; --faint:#6e6e73;
  --blue:#0a84ff; --green:#30d158; --orange:#ff9f0a; --red:#ff453a;
}

/* ---------- 全局 ---------- */
.stApp {
  background:
    radial-gradient(1200px 560px at 82% -10%, rgba(10,132,255,.07), transparent 62%),
    radial-gradient(900px 480px at 6% 110%, rgba(191,90,242,.05), transparent 58%),
    var(--bg);
}
html, body, .stApp, [class*="css"] {
  font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','PingFang SC',
    'Segoe UI',system-ui,sans-serif;
  color: var(--txt);
  -webkit-font-smoothing:antialiased;
}
.block-container { padding-top:1.1rem; max-width:1400px; }
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"] { background:transparent; }
hr { border-color:var(--line); }
::selection { background:rgba(10,132,255,.35); }
::-webkit-scrollbar { width:10px; height:10px; }
::-webkit-scrollbar-thumb {
  background:rgba(255,255,255,.16); border-radius:8px;
  border:3px solid transparent; background-clip:content-box;
}
::-webkit-scrollbar-track { background:transparent; }

/* ---------- 玻璃面板基元 ---------- */
.glass, .stat-card, .theme-card, .gain-card {
  background:var(--panel);
  -webkit-backdrop-filter:blur(24px) saturate(150%);
  backdrop-filter:blur(24px) saturate(150%);
  border:1px solid var(--line);
  border-radius:18px;
  box-shadow:0 8px 30px rgba(0,0,0,.35);
}

/* ---------- 侧边栏 ---------- */
section[data-testid="stSidebar"] {
  background:rgba(18,18,21,.72);
  -webkit-backdrop-filter:blur(28px) saturate(150%);
  backdrop-filter:blur(28px) saturate(150%);
  border-right:1px solid var(--line);
}
section[data-testid="stSidebar"] * { color:var(--txt); }
section[data-testid="stSidebar"] hr { margin:.4rem 0; border-color:var(--line); }
/* 侧边栏纵向节奏收紧，保证配置一屏放下 */
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:.4rem !important; }
section[data-testid="stSidebar"] h2 { font-size:1.02rem; margin-bottom:0; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { margin-bottom:0; }

/* ---------- Hero 头部 ---------- */
.hero { padding:.15rem 0 .1rem 0; }
.hero-badge {
  display:inline-flex; align-items:center; gap:.5em;
  font-size:11px; font-weight:600; letter-spacing:.14em;
  color:var(--sub);
  border:1px solid var(--line); border-radius:999px;
  padding:.34em 1em; margin-bottom:.6em;
  background:var(--panel);
}
.hero-dot { width:7px; height:7px; border-radius:50%; background:var(--green);
  animation:pulse 2.4s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
@media (prefers-reduced-motion: reduce) {
  .hero-dot { animation:none; }
  .stat-card, .theme-card, .gain-card { transition:none; }
}
.hero h1 {
  font-size:1.9rem; font-weight:700; line-height:1.18; margin:0 0 .3rem 0;
  color:var(--txt); letter-spacing:-.02em;
}
.hero-sub { color:var(--sub); font-size:.9rem; letter-spacing:0; }

/* ---------- 统计卡 ---------- */
.stat-grid { display:flex; gap:13px; flex-wrap:wrap; margin:.35rem 0 1rem 0; }
.stat-card { flex:1 1 160px; min-width:158px; padding:16px 18px 14px; }
.stat-num {
  font-size:27px; font-weight:600; color:var(--txt);
  letter-spacing:-.02em; font-variant-numeric:tabular-nums;
}
.stat-num small { font-size:15px; color:var(--sub); font-weight:500; }
.stat-label { margin-top:5px; font-size:12px; font-weight:500; color:var(--sub); }

/* ---------- 主题洞察卡 ---------- */
.theme-card { padding:16px 19px; margin-bottom:13px; }
.theme-head { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.theme-name { font-size:1.05rem; font-weight:600; color:var(--txt); letter-spacing:-.01em; }
.badge {
  font-size:11px; font-weight:600;
  padding:.25em .75em; border-radius:999px; border:1px solid;
}
.freq { margin-left:auto; color:var(--faint); font-size:12px;
  font-variant-numeric:tabular-nums; }
.sev-high { color:var(--red); border-color:rgba(255,69,58,.35); background:rgba(255,69,58,.12); }
.sev-mid  { color:var(--orange); border-color:rgba(255,159,10,.35); background:rgba(255,159,10,.12); }
.sev-low  { color:var(--blue); border-color:rgba(10,132,255,.35); background:rgba(10,132,255,.12); }
.theme-insight { margin:.65rem 0 .2rem; color:#d1d1d6; font-size:.93rem;
  border-left:2px solid var(--ac,var(--blue)); padding-left:.75em; }
.quote { color:var(--sub); font-size:.84rem; margin-top:.3rem; padding-left:1em; }

/* ---------- Star 增幅榜 ---------- */
.section-head { display:flex; align-items:baseline; gap:14px; flex-wrap:wrap;
  margin:.15rem 0 .7rem; }
.section-title {
  font-size:1.3rem; font-weight:700; letter-spacing:-.02em; color:var(--txt);
}
.section-sub { color:var(--sub); font-size:.8rem; }
.gain-card {
  position:relative; overflow:hidden; height:100%;
  padding:10px 14px 9px 54px;
  transition:background .18s ease, transform .18s ease;
}
.gain-card:hover {
  background:var(--panel-strong); transform:translateY(-1px);
}
.gain-rank {
  position:absolute; left:16px; top:50%; transform:translateY(-50%);
  font-size:19px; font-weight:700; color:var(--rc,var(--faint));
  font-variant-numeric:tabular-nums; letter-spacing:-.02em;
}
.gain-name {
  font-size:1rem; font-weight:600; color:var(--txt);
  text-decoration:none; word-break:break-all; letter-spacing:-.01em;
}
.gain-name:hover { color:var(--blue); }
.gain-meta {
  margin-top:3px; font-size:12px; color:var(--sub);
  font-variant-numeric:tabular-nums;
}
.gain-meta b { color:var(--green); font-weight:600; font-size:13px; }
.gain-desc {
  margin-top:3px; color:var(--sub); font-size:.83rem; line-height:1.45;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
}
.board-tag {
  display:inline-block; margin-left:8px; vertical-align:1px;
  font-size:10px; font-weight:600; letter-spacing:.04em;
  padding:.14em .6em; border-radius:999px;
}
.tag-new { color:var(--green); background:rgba(48,209,88,.12);
  border:1px solid rgba(48,209,88,.35); }
.tag-streak { color:var(--sub); background:rgba(255,255,255,.06);
  border:1px solid var(--line); font-variant-numeric:tabular-nums; }
.lang-dot {
  display:inline-block; width:8px; height:8px; border-radius:50%;
  background:var(--lc,#8e8e93); margin-right:5px;
}
/* 榜单卡右侧 ➕ 图标按钮：按钮列很窄且带 help tooltip 包装层，
   须压缩内边距并单独着色，否则图标被裁切；标签为纯文本 + 字形随主题 */
[data-testid="stHorizontalBlock"]:has(.gain-card) .stButton button {
  min-width:0; padding:2px 7px; font-size:18px; font-weight:500; line-height:1.3;
  border:1px solid var(--line); border-radius:10px;
  background:rgba(255,255,255,.07); color:var(--txt); box-shadow:none;
}
[data-testid="stHorizontalBlock"]:has(.gain-card) .stButton button:hover {
  background:rgba(255,255,255,.14); border-color:var(--line-strong);
}
/* 榜单标题右侧刷新按钮：与卡片 ➕ 同款的小方块 ghost 图标钮，
   借 st-key-* 包装类精准命中，覆盖全局主按钮样式 */
.st-key-refresh_hot .stButton button {
  width:auto; min-width:0; min-height:0; padding:4px 11px; font-size:17px;
  font-weight:600; line-height:1.2;
  border:1px solid var(--line); border-radius:10px;
  background:rgba(255,255,255,.07); color:var(--txt); box-shadow:none;
}
.st-key-refresh_hot .stButton button:hover {
  background:rgba(255,255,255,.14); border-color:var(--line-strong);
}

/* ---------- Tab：iOS 分段控件（Streamlit 1.62+ 新 DOM，stTab/stTabPanel） ---------- */
[data-testid="stTabs"] div:has(> [data-testid="stTab"]) {
  gap:4px; background:rgba(255,255,255,.05);
  border:1px solid var(--line); border-radius:12px; padding:4px;
  width:fit-content;
}
[data-testid="stTab"] {
  border:none; border-radius:9px; padding:6px 18px;
  background:transparent; color:var(--sub); font-weight:500;
}
[data-testid="stTab"] p { margin:0; }
[data-testid="stTab"]:hover { color:var(--txt); }
[data-testid="stTab"][aria-selected="true"] {
  color:var(--txt) !important; background:rgba(255,255,255,.14);
  box-shadow:0 1px 4px rgba(0,0,0,.35);
}
/* 关掉 React Aria 自带的选中下划线，选中态由玻璃亮块表达 */
[data-testid="stTab"] .react-aria-SelectionIndicator { display:none; }

/* ---------- 主按钮：玻璃质感胶囊（磨砂半透 + 背景模糊，与卡片同体系） ---------- */
.stButton > button {
  width:100%; border:1px solid var(--line-strong); border-radius:980px;
  font-weight:600; color:var(--txt);
  background:rgba(255,255,255,.12);
  -webkit-backdrop-filter:blur(24px) saturate(150%);
  backdrop-filter:blur(24px) saturate(150%);
  box-shadow:0 8px 30px rgba(0,0,0,.35);
  transition:background .15s ease;
}
.stButton > button:hover { background:rgba(255,255,255,.2); }
/* ---------- 手机端适配（≤640px，Streamlit 列堆叠断点） ---------- */
@media (max-width: 640px) {
  .hero h1 { font-size:1.5rem; }
  .hero-sub { display:none; }  /* 副标题折行占地，手机端隐藏 */
  /* ➕ 按钮列隐藏：窄屏列堆叠后它脱离卡片独占一条全宽灰杠，
     而「加仓库到分析目标」是桌面场景，手机上看榜不需要 */
  [data-testid="stHorizontalBlock"]:has(.gain-card)
    > [data-testid="stColumn"]:not(:has(.gain-card)) { display:none; }
}

/* ---------- 输入控件 ---------- */
.stDownloadButton > button {
  width:100%; border:1px solid var(--line-strong); border-radius:980px;
  background:rgba(255,255,255,.06); color:var(--txt); font-weight:600;
}
.stDownloadButton > button:hover { background:rgba(255,255,255,.1); }
input, textarea { border-radius:12px !important; }
"""


def inject() -> None:
    """注入全局样式（在 set_page_config 之后调用一次）。"""
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(badge: str, title: str, sub: str) -> None:
    """页面顶部大标题；badge 为空串时不渲染徽章行。"""
    def esc(s: object) -> str:
        return _html.escape(str(s))
    badge_html = (
        f'<div class="hero-badge"><span class="hero-dot"></span>{esc(badge)}</div>'
        if badge
        else ""
    )
    st.markdown(
        '<div class="hero">'
        f'{badge_html}'
        f'<h1>{esc(title)}</h1>'
        f'<div class="hero-sub">{esc(sub)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def stat_cards(items: list[tuple[str, str, str]]) -> None:
    """一行磨砂玻璃统计卡。items: [(标签, 数值, 强调色)]。"""
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
    """Star 增幅榜单卡 HTML。rank 1-3 用金/银/铜名次色，其余中性灰；
    days_on_board=1 标 NEW，>1 标连续天数，None（冷启动）不标。"""
    esc = _html.escape
    rank_color = {1: "#ffd60a", 2: "#b8b8bd", 3: "#ff9f0a"}.get(rank, "#48484a")
    desc = (item.get("description") or "").strip()
    lang = (item.get("language") or "").strip()
    days = item.get("days_on_board")
    if days == 1:
        tag = '<span class="board-tag tag-new">NEW</span>'
    elif isinstance(days, int) and days > 1:
        tag = f'<span class="board-tag tag-streak">×{days} 天</span>'
    else:
        tag = ""
    if lang and lang != "-":
        dot = f'<span class="lang-dot" style="--lc:{LANG_COLORS.get(lang, "#8e8e93")}"></span>'
        lang_txt = esc(lang)
    else:
        dot, lang_txt = "", "-"
    return (
        f'<div class="gain-card" style="--rc:{rank_color}">'
        f'<div class="gain-rank">{rank:02d}</div>'
        f'<a class="gain-name" href="{esc(item.get("url", "#"))}" target="_blank">'
        f'{esc(item.get("repo", "?"))}</a>{tag}'
        f'<div class="gain-meta"><b>+{int(item.get("gained", 0)):,}</b> ⭐ 今日'
        f' · 全站 {int(item.get("stars", 0)):,}'
        f' · {dot}{lang_txt}</div>'
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
