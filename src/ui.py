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
  --bg:#0d1016; --panel:rgba(255,255,255,.052); --panel-strong:rgba(255,255,255,.09);
  --line:rgba(255,255,255,.12); --line-strong:rgba(255,255,255,.2);
  --txt:#f5f5f7; --sub:#a1a1a6; --faint:#6e6e73;
  --blue:#0a84ff; --green:#30d158; --orange:#ff9f0a; --red:#ff453a;
  --font-ui:-apple-system,BlinkMacSystemFont,'SF Pro Text','PingFang SC','Segoe UI',system-ui,sans-serif;
  --text-small:.78rem;
}

/* ---------- 全局 ---------- */
.stApp {
  background:
    radial-gradient(ellipse 72% 38% at 54% -8%, rgba(85,115,162,.16), transparent 68%),
    radial-gradient(ellipse 28% 42% at 4% 42%, rgba(30,86,143,.09), transparent 72%),
    radial-gradient(ellipse 32% 38% at 96% 76%, rgba(93,71,126,.07), transparent 74%),
    linear-gradient(155deg,#111722 0%,#0c0f15 48%,#111116 100%);
}
html, body, .stApp, [class*="css"] {
  font-family:var(--font-ui);
  color: var(--txt);
  -webkit-font-smoothing:antialiased;
}
.stApp { line-height:1.55; }
.stApp h1, .stApp h2, .stApp h3 { line-height:1.2; letter-spacing:-.025em; }
.stApp h2 { font-size:1.25rem; font-weight:650; }
.stApp h3 { font-size:1.05rem; font-weight:620; }
.stApp [data-testid="stCaptionContainer"] { color:var(--sub); font-size:var(--text-small); }
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
  background:
    linear-gradient(138deg,rgba(255,255,255,.095) 0%,rgba(255,255,255,.045) 32%,rgba(255,255,255,.018) 76%),
    rgba(24,29,39,.42);
  -webkit-backdrop-filter:blur(30px) saturate(165%);
  backdrop-filter:blur(30px) saturate(165%);
  border:1px solid rgba(255,255,255,.15);
  border-radius:18px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.16),
    inset 0 -1px 0 rgba(255,255,255,.025),
    0 10px 28px rgba(0,0,0,.3),0 26px 54px rgba(0,0,0,.16);
}

/* ---------- 侧边栏 ---------- */
section[data-testid="stSidebar"] {
  background:linear-gradient(155deg,rgba(255,255,255,.075),rgba(19,23,31,.78) 38%,rgba(14,16,22,.72));
  -webkit-backdrop-filter:blur(32px) saturate(170%);
  backdrop-filter:blur(32px) saturate(170%);
  border-right:1px solid rgba(255,255,255,.14);
  box-shadow:inset -1px 0 0 rgba(255,255,255,.035),8px 0 30px rgba(0,0,0,.12);
}
section[data-testid="stSidebar"] * { color:var(--txt); }
section[data-testid="stSidebar"] hr { margin:.4rem 0; border-color:var(--line); }
/* 侧边栏纵向节奏收紧，保证配置一屏放下（只压 label，caption 保留间距防重叠） */
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:.4rem !important; }
section[data-testid="stSidebar"] h2 { font-size:1.02rem; margin-bottom:0; }
section[data-testid="stSidebar"] label { margin-bottom:0; }
/* expander 与上方 caption 之间留出明确间隔，防止行高贴边重叠 */
section[data-testid="stSidebar"] [data-testid="stExpander"] { margin-top:.6rem; }

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
  .hero-dot, .signal-item i { animation:none; }
  .stat-card, .theme-card, .gain-card { transition:none; }
}
.hero h1 {
  font-size:1.9rem; font-weight:700; line-height:1.18; margin:0 0 .3rem 0;
  color:var(--txt); letter-spacing:-.02em;
}
.hero-sub { color:var(--sub); font-size:.9rem; letter-spacing:0; }

/* 首页主视觉：用真实榜单数据构成信号脉冲，而不是装饰性渐变 */
.intel-hero { display:grid; grid-template-columns:minmax(0,1fr) minmax(260px,.62fr);
  gap:28px; align-items:center; padding:22px 24px; margin:.1rem 0 1.25rem;
  border:1px solid rgba(255,255,255,.19); border-radius:22px;
  background:radial-gradient(ellipse 72% 120% at 100% 0%,rgba(255,159,10,.13),transparent 68%),
    linear-gradient(122deg,rgba(255,255,255,.12),rgba(73,103,148,.08) 38%,rgba(255,255,255,.025) 78%),rgba(20,25,35,.34);
  -webkit-backdrop-filter:blur(34px) saturate(175%); backdrop-filter:blur(34px) saturate(175%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.19),inset 0 -1px 0 rgba(255,255,255,.035),
    0 20px 48px rgba(0,0,0,.34),0 3px 12px rgba(0,0,0,.2); }
.intel-copy .hero { padding:0; }
.intel-kicker { display:inline-flex; align-items:center; gap:8px; margin-bottom:.8rem;
  padding:6px 10px; border:1px solid rgba(255,255,255,.13); border-radius:999px;
  background:rgba(255,255,255,.045); color:#c5d2c9; font-size:.72rem; font-weight:550; }
.intel-kicker .hero-dot { width:6px; height:6px; flex:none; }
.intel-kicker i { color:var(--sub); font-style:normal; }
.intel-copy .hero h1 { font-size:2.2rem; line-height:1.08; letter-spacing:-.045em; }
.intel-title-line { display:block; }
.intel-title-line + .intel-title-line { color:#d8dfeb; font-size:.88em; letter-spacing:-.035em; }
.intel-subjects { display:flex; flex-wrap:wrap; align-items:center; gap:7px; margin-top:15px; }
.intel-subject { display:inline-flex; align-items:center; gap:6px; color:#c4c9d2;
  border:1px solid rgba(255,255,255,.1); border-radius:8px; padding:5px 8px;
  background:rgba(255,255,255,.035); font-size:.7rem; }
.intel-subject::before { content:""; width:4px; height:4px; border-radius:50%; background:var(--orange); }
.signal-panel { padding:15px 17px; border-left:1px solid var(--line-strong); }
.signal-top { display:flex; justify-content:space-between; align-items:baseline; gap:12px; }
.signal-label { font-size:.78rem; color:var(--sub); }
.signal-value { font-size:1.55rem; font-weight:650; font-variant-numeric:tabular-nums; }
.signal-top .signal-value { color:#ffd08a; text-shadow:0 0 22px rgba(255,159,10,.18); }
.signal-unit { color:var(--sub); font-size:.78rem; margin-left:5px; }
.signal-scale { display:flex; justify-content:space-between; color:var(--faint); font-size:.68rem; margin-top:8px; }
.signal-bars { height:52px; display:flex; align-items:end; gap:5px; margin:2px 0 0;
  border-bottom:1px solid var(--line-strong); }
.signal-item { flex:1; min-width:4px; height:100%; display:flex; flex-direction:column;
  justify-content:end; align-items:center; gap:3px; }
.signal-item i { display:block; width:100%; max-width:22px; min-height:3px;
  border-radius:3px 3px 1px 1px;
  background:rgba(48,209,88,.72); transform-origin:bottom;
  animation:signal-rise .65s cubic-bezier(.2,.75,.25,1) both; }
.signal-item:nth-child(2) i { animation-delay:45ms; }
.signal-item:nth-child(3) i { animation-delay:90ms; }
.signal-item:nth-child(4) i { animation-delay:135ms; }
.signal-item:nth-child(5) i { animation-delay:180ms; }
.signal-item:nth-child(6) i { animation-delay:225ms; }
.signal-item:nth-child(7) i { animation-delay:270ms; }
.signal-item:nth-child(8) i { animation-delay:315ms; }
.signal-item:first-child i { background:rgba(255,159,10,.9); }
@keyframes signal-rise { from { transform:scaleY(.15); opacity:.35; } to { transform:scaleY(1); opacity:1; } }
.signal-item small { color:var(--faint); font-size:.62rem; line-height:1; }
.signal-feature { display:flex; align-items:flex-start; gap:9px; margin-top:10px; }
.signal-rank { color:var(--orange); font-size:.7rem; font-weight:700; padding-top:2px; }
.signal-feature-copy { min-width:0; }
.signal-repo { color:var(--txt); font-size:.84rem; font-weight:600; text-decoration:none;
  overflow-wrap:anywhere; }
.signal-repo:hover { color:var(--blue); }
.signal-description { color:var(--sub); font-size:.7rem; line-height:1.4; margin-top:2px;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.signal-foot { display:flex; justify-content:space-between; gap:8px; color:var(--faint); font-size:.72rem; margin-top:7px; }
.focus-card { display:grid; grid-template-columns:170px minmax(0,1fr); gap:18px;
  align-items:start; padding:14px 18px; margin:0 0 .7rem;
  border:1px solid rgba(255,255,255,.12); border-left:2px solid var(--orange);
  background:linear-gradient(120deg,rgba(255,159,10,.09),rgba(255,255,255,.035) 52%),rgba(24,27,34,.32);
  -webkit-backdrop-filter:blur(24px) saturate(155%); backdrop-filter:blur(24px) saturate(155%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 8px 22px rgba(0,0,0,.18); }
.focus-label { color:var(--orange); font-size:.78rem; font-weight:600; }
.focus-main { color:var(--txt); font-size:.96rem; font-weight:600; }
.focus-detail { color:var(--sub); font-size:.82rem; line-height:1.55; margin-top:3px; }
.focus-empty { border-left-color:var(--blue);
  background:linear-gradient(120deg,rgba(10,132,255,.09),rgba(255,255,255,.035) 52%),rgba(24,27,34,.32); }
.focus-empty .focus-label { color:var(--blue); }
.home-action-copy { color:var(--sub); font-size:.84rem; line-height:1.5; }

/* ---------- 统计卡 ---------- */
.stat-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:0;
  margin:.35rem 0 1.1rem; padding:5px 0;
  border:1px solid rgba(255,255,255,.11); border-radius:15px;
  background:linear-gradient(110deg,rgba(255,255,255,.055),rgba(255,255,255,.018)),rgba(18,22,29,.4);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.08); }
.stat-card { min-width:0; padding:13px 16px 12px; background:transparent;
  -webkit-backdrop-filter:none; backdrop-filter:none; border:0; border-radius:0; box-shadow:none; }
.stat-card:not(:last-child) { border-right:1px solid rgba(255,255,255,.09); }
.stat-num {
  font-size:25px; font-weight:650; color:var(--txt);
  letter-spacing:-.02em; font-variant-numeric:tabular-nums;
}
.stat-num small { font-size:15px; color:var(--sub); font-weight:500; }
.stat-label { margin-top:5px; font-size:12px; font-weight:500; color:var(--sub); }

/* ---------- 主题洞察卡 ---------- */
.theme-card { padding:15px 18px; margin-bottom:11px; border-radius:13px;
  background:linear-gradient(120deg,rgba(255,255,255,.048),rgba(255,255,255,.018)),rgba(18,22,29,.28);
  -webkit-backdrop-filter:blur(20px) saturate(145%); backdrop-filter:blur(20px) saturate(145%);
  border-color:rgba(255,255,255,.09); box-shadow:inset 0 1px 0 rgba(255,255,255,.075),0 5px 15px rgba(0,0,0,.16); }
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
  margin:.35rem 0 .85rem; padding:0 0 .65rem;
  border-bottom:1px solid rgba(255,255,255,.09); }
.section-title {
  font-size:1.32rem; font-weight:700; letter-spacing:-.025em; color:var(--txt);
}
.section-sub { color:var(--sub); font-size:.8rem; }
.gain-card {
  position:relative; overflow:hidden; height:100%; min-height:142px;
  padding:10px 14px 9px 54px;
  display:flex; flex-direction:column; align-items:stretch;
  background:linear-gradient(145deg,rgba(255,255,255,.065),rgba(255,255,255,.018)),rgba(19,23,31,.38);
  border-color:rgba(255,255,255,.105); border-radius:15px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.09),0 7px 20px rgba(0,0,0,.2);
  transition:background .18s ease, border-color .18s ease, transform .18s ease;
}
.gain-card:hover {
  background:linear-gradient(145deg,rgba(255,255,255,.1),rgba(255,255,255,.03)),rgba(19,23,31,.48);
  border-color:var(--line-strong); transform:translateY(-2px);
}
.gain-top-1 { border-color:rgba(255,159,10,.4); border-radius:17px;
  background:radial-gradient(ellipse 90% 75% at 0% 0%,rgba(255,159,10,.13),transparent 72%),
    linear-gradient(145deg,rgba(255,255,255,.09),rgba(255,255,255,.025)),rgba(26,25,27,.46);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.14),inset 2px 0 0 rgba(255,159,10,.7),
    0 10px 26px rgba(0,0,0,.24),0 0 24px rgba(255,159,10,.045); }
.gain-top-2 { border-color:rgba(214,222,235,.22); }
.gain-top-3 { border-color:rgba(205,128,82,.24); }
.gain-top-1 .gain-rank { font-size:22px; text-shadow:0 0 18px rgba(255,159,10,.25); }
.gain-card a:focus-visible { outline:2px solid var(--blue); outline-offset:3px; border-radius:3px; }
.gain-rank {
  position:absolute; left:16px; top:50%; transform:translateY(-50%);
  font-size:19px; font-weight:700; color:var(--rc,var(--faint));
  font-variant-numeric:tabular-nums; letter-spacing:-.02em;
}
.gain-head { display:flex; align-items:center; gap:8px; min-width:0; min-height:24px; }
.gain-name {
  min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  font-size:1rem; font-weight:600; color:var(--txt);
  text-decoration:none; letter-spacing:-.01em;
}
.gain-name:hover { color:var(--blue); }
.gain-head .board-tag { flex:none; margin-left:0; }
.gain-meta {
  min-height:19px; margin-top:3px; font-size:12px; color:var(--sub);
  font-variant-numeric:tabular-nums;
}
.gain-meta b { color:var(--green); font-weight:600; font-size:13px; }
.gain-desc {
  min-height:2.9em; margin-top:3px; color:var(--sub); font-size:.83rem; line-height:1.45;
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
.topic-row { margin-top:auto; min-height:19px; padding-top:6px; display:flex; gap:6px; flex-wrap:wrap; }
.topic-chip {
  font-size:10.5px; color:var(--sub);
  background:rgba(255,255,255,.06); border:1px solid var(--line);
  border-radius:6px; padding:.14em .55em;
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
  background:linear-gradient(145deg,rgba(255,255,255,.18),rgba(255,255,255,.075));
  -webkit-backdrop-filter:blur(24px) saturate(150%);
  backdrop-filter:blur(24px) saturate(150%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.2),0 8px 24px rgba(0,0,0,.32);
  transition:background .15s ease;
}
.stButton > button:hover { background:rgba(255,255,255,.2); }
/* ---------- 手机端适配（≤640px，Streamlit 列堆叠断点） ---------- */
@media (max-width: 640px) {
  .intel-hero { grid-template-columns:1fr; gap:12px; padding:18px; }
  .intel-copy .hero h1 { font-size:1.5rem; }
  .signal-panel { border-left:0; border-top:1px solid var(--line); padding:12px 0 0; }
  .focus-card { grid-template-columns:1fr; gap:4px; }
  .hero h1 { font-size:1.5rem; }
  .hero-sub { display:none; }  /* 副标题折行占地，手机端隐藏 */
  /* 手机端增加呼吸感：页头与侧栏间距恢复常态（桌面紧凑化不适用于触屏小窗） */
  .block-container { padding-top:1.3rem; }
  .stat-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .stat-card:nth-child(3n) { border-right:1px solid rgba(255,255,255,.09); }
  .stat-card:nth-child(2n) { border-right:0; }
  .stat-card:nth-child(n+3) { border-top:1px solid rgba(255,255,255,.09); }
  .stat-card { padding:12px 11px; }
  .stat-num { font-size:22px; }
  section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:.75rem !important; }
  /* ➕ 按钮列隐藏：窄屏列堆叠后它脱离卡片独占一条全宽灰杠，
     而「加仓库到分析目标」是桌面场景，手机上看榜不需要 */
  [data-testid="stHorizontalBlock"]:has(.gain-card)
    > [data-testid="stColumn"]:not(:has(.gain-card)) { display:none; }
}
@media (min-width: 641px) and (max-width: 900px) {
  .stat-grid { grid-template-columns:repeat(3,minmax(0,1fr)); }
  .stat-card:nth-child(3n) { border-right:0; }
  .stat-card:nth-child(n+4) { border-top:1px solid rgba(255,255,255,.09); }
}

/* ---------- 输入控件 ---------- */
section[data-testid="stSidebar"] [data-testid="stTextInput"] [data-baseweb="input"] > div,
section[data-testid="stSidebar"] [data-testid="stTextArea"] textarea,
section[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {
  background:linear-gradient(145deg,rgba(255,255,255,.075),rgba(255,255,255,.025)) !important;
  border:1px solid rgba(255,255,255,.12) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.075);
  -webkit-backdrop-filter:blur(18px) saturate(145%);
  backdrop-filter:blur(18px) saturate(145%);
}
section[data-testid="stSidebar"] [data-baseweb="input"]:focus-within,
section[data-testid="stSidebar"] [data-baseweb="select"]:focus-within {
  border-color:rgba(10,132,255,.55) !important;
  box-shadow:0 0 0 2px rgba(10,132,255,.14),inset 0 1px 0 rgba(255,255,255,.1);
}
.stDownloadButton > button {
  width:100%; border:1px solid var(--line-strong); border-radius:980px;
  background:rgba(255,255,255,.06); color:var(--txt); font-weight:600;
}
.stDownloadButton > button:hover { background:rgba(255,255,255,.1); }
input, textarea { border-radius:12px !important; }
@media (prefers-reduced-motion: reduce) {
  .hero-dot, .signal-item i { animation:none; }
  .gain-card { transition:none; }
}
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


def intel_hero(items: list[dict], updated_at: object = None) -> None:
    """首页情报焦点：摘要与榜单前列的真实增幅构成轻量信号图。"""
    esc = _html.escape
    values = [max(0, int(item.get("gained", 0))) for item in items[:8]]
    peak = max(values, default=0)
    bars = "".join(
        f'<span class="signal-item"><i title="榜单第{rank}：+{value:,} stars" '
        f'aria-label="榜单第{rank}：+{value:,} stars" '
        f'style="height:{max(6, round(value / peak * 78)) if peak else 6}%"></i>'
        f'<small>{rank}</small></span>'
        for rank, value in enumerate(values, start=1)
    )
    top_repo = esc(items[0].get("repo", "暂无榜首数据")) if items else "暂无榜首数据"
    top_url = str(items[0].get("url", "")) if items else ""
    top_description = esc(items[0].get("description", "")) if items else ""
    repo_html = (
        f'<a class="signal-repo" href="{esc(top_url)}" target="_blank" rel="noopener noreferrer">'
        f'{top_repo} ↗</a>'
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
        '<div class="intel-copy"><div class="intel-kicker"><span class="hero-dot"></span>'
        '<span>社区信号</span><i>实时观察</i></div>'
        '<div class="hero"><h1><span class="intel-title-line">Open Source</span>'
        '<span class="intel-title-line">Pain Intelligence</span></h1>'
        '<div class="hero-sub">从 GitHub Issue 与项目热度中，发现正在升温的需求和问题。</div>'
        '<div class="intel-subjects"><span class="intel-subject">GitHub Issues</span>'
        '<span class="intel-subject">Star 增长</span><span class="intel-subject">社区需求</span></div></div>'
        '</div><div class="signal-panel"><div class="signal-top">'
        '<span class="signal-label">今日 Star 增幅榜首</span>'
        f'<span><b class="signal-value">{peak_text}</b><span class="signal-unit">stars</span></span>'
        f'</div><div class="signal-scale"><span>增幅</span><span>最高 {peak_text}</span></div>'
        f'<div class="signal-bars" aria-label="柱体按榜单排名排列，悬停查看 Star 增幅">{bars}</div>'
        f'<div class="signal-feature"><span class="signal-rank">#1</span>'
        f'<div class="signal-feature-copy">{repo_html}'
        f'{description_html}'
        '</div></div>'
        f'<div class="signal-foot"><span>Top {len(values)} · 按日增 Star 排序</span>'
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
        label = f"优先关注 · {severity}风险 · {int(theme.get('frequency', 0))} 条 Issue"
        name = esc(theme.get("name", "未命名主题"))
        detail = esc(theme.get("insight", ""))
        css = "focus-card"
    elif result:
        label, name = "本次分析", "暂未识别出缺陷类主题"
        detail = "可以查看功能诉求、趋势与情绪板块，了解这批 Issue 的其他信号。"
        css = "focus-card focus-empty"
    else:
        label, name = "等待首次分析", "这里会显示最值得优先关注的社区痛点。"
        detail = "先在左侧配置目标仓库和模型，再点击下方「开始分析 Issue」。"
        css = "focus-card focus-empty"
    st.markdown(
        f'<div class="{css}"><div class="focus-label">{esc(label)}</div>'
        f'<div><div class="focus-main">{name}</div>'
        f'<div class="focus-detail">{detail}</div></div></div>',
        unsafe_allow_html=True,
    )


_SEVERITY_ORDER = {"高": 0, "中": 1, "低": 2}


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
    topics = [esc(t) for t in (item.get("topics") or [])[:4]]
    chips = "".join(f'<span class="topic-chip">#{t}</span>' for t in topics)
    topic_row = f'<div class="topic-row">{chips}</div>'
    if lang and lang != "-":
        dot = f'<span class="lang-dot" style="--lc:{LANG_COLORS.get(lang, "#8e8e93")}"></span>'
        lang_txt = esc(lang)
    else:
        dot, lang_txt = "", "-"
    return (
        f'<div class="gain-card gain-top-{rank}" style="--rc:{rank_color}">'
        f'<div class="gain-rank">{rank:02d}</div>'
        '<div class="gain-head">'
        f'<a class="gain-name" href="{esc(item.get("url", "#"))}" target="_blank" '
        f'title="{esc(item.get("repo", "?"))}">{esc(item.get("repo", "?"))}</a>{tag}</div>'
        f'<div class="gain-meta"><b>+{int(item.get("gained", 0)):,}</b> ⭐ 今日'
        f' · 全站 {int(item.get("stars", 0)):,}'
        f' · {dot}{lang_txt}</div>'
        + f'<div class="gain-desc">{esc(desc)}</div>'
        + topic_row
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
