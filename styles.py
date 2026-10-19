"""All CSS for HireFlow (kept out of app.py so the UI code stays readable)."""
from urllib.parse import quote

# Feather-style line icons used as masks for the sidebar menu (one per page, in menu order).
_ICONS = [
    "<rect x='3' y='3' width='7' height='7' rx='1'/><rect x='14' y='3' width='7' height='7' rx='1'/>"
    "<rect x='14' y='14' width='7' height='7' rx='1'/><rect x='3' y='14' width='7' height='7' rx='1'/>",
    "<path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/>"
    "<path d='M23 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/>",
    "<rect x='3' y='3' width='18' height='18' rx='2'/><line x1='9' y1='3' x2='9' y2='21'/>"
    "<line x1='15' y1='3' x2='15' y2='21'/>",
    "<path d='M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='8.5' cy='7' r='4'/>"
    "<line x1='20' y1='8' x2='20' y2='14'/><line x1='23' y1='11' x2='17' y2='11'/>",
    "<path d='M7 16V4m0 0L3 8m4-4 4 4'/><path d='M17 8v12m0 0 4-4m-4 4-4-4'/>",
]


def _icon_css() -> str:
    out = []
    for i, body in enumerate(_ICONS, start=1):
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
               f"stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{body}</svg>")
        url = f'url("data:image/svg+xml,{quote(svg)}")'
        out.append(f'[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child({i}) label > div::before'
                   f'{{-webkit-mask-image:{url};mask-image:{url};}}')
    return "\n".join(out)


BASE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
@property --n { syntax:'<integer>'; initial-value:0; inherits:false; }

html { scroll-behavior:smooth; }
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp input, .stApp textarea, .stApp button, .stApp td, .stApp th, .stMarkdown,
[data-testid="stCaptionContainer"], [data-baseweb] {
  font-family:'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif !important; }
.stApp { background:#F6F7F9; color:#111827; font-size:15px; }
.block-container { padding-top:4.2rem; padding-bottom:2rem; max-width:1240px; }

/* ---------- keyframes ---------- */
@keyframes fadeUp { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:none; } }
@keyframes slideIn { from { opacity:0; transform:translateX(-14px); } to { opacity:1; transform:none; } }
@keyframes countup { from { --n:0; } }
@keyframes pulse { 0% { box-shadow:0 0 0 0 rgba(34,197,94,.55); } 70% { box-shadow:0 0 0 8px rgba(34,197,94,0); }
                   100% { box-shadow:0 0 0 0 rgba(34,197,94,0); } }
@keyframes shimmer { from { background-position:200% 0; } to { background-position:-200% 0; } }

/* ---------- page transition: content fades up, one block after another ---------- */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > * { animation:fadeUp .55s cubic-bezier(.22,1,.36,1) both; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(2) { animation-delay:.04s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(3) { animation-delay:.08s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(4) { animation-delay:.12s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(5) { animation-delay:.16s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(6) { animation-delay:.20s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(n+7) { animation-delay:.24s; }

/* ---------- native header = translucent bar ---------- */
[data-testid="stHeader"] { background:rgba(246,247,249,.78); backdrop-filter:blur(10px); border-bottom:1px solid #E5E7EB; }
[data-testid="stAppDeployButton"] { display:none; }

/* ---------- typography ---------- */
h1 { font-size:1.9rem !important; font-weight:700 !important; letter-spacing:-0.02em; color:#111827; padding-bottom:0 !important; }
h3 { font-size:1.05rem !important; font-weight:600 !important; color:#111827; padding-top:.2rem !important; }
.eyebrow { font-size:.75rem; font-weight:600; color:#6B7280; letter-spacing:.08em; text-transform:uppercase; margin-bottom:2px; }
.subtitle { color:#6B7280; font-size:.95rem; margin:-.3rem 0 1.4rem 0; }
.muted { color:#6B7280; font-size:.82rem; }

/* ---------- top bar ---------- */
.topbar { display:flex; justify-content:space-between; align-items:center; background:#FFFFFF; border:1px solid #E5E7EB;
  border-radius:14px; padding:10px 16px; margin-bottom:1.6rem; box-shadow:0 1px 2px rgba(15,23,42,.04); }
.crumb { font-size:.9rem; color:#6B7280; display:flex; gap:8px; align-items:center; }
.crumb b { color:#111827; font-weight:600; }
.crumb .sep { color:#D1D5DB; }
.top-right { display:flex; align-items:center; gap:12px; }
.chip { display:inline-flex; align-items:center; gap:7px; background:#F0FDF4; color:#166534; border:1px solid #BBF7D0;
  padding:3px 11px; border-radius:999px; font-size:.78rem; font-weight:600; }
.dot { width:8px; height:8px; border-radius:50%; background:#22C55E; display:inline-block; animation:pulse 2s infinite; }
.datepill { font-size:.82rem; color:#6B7280; }
.avatar { width:34px; height:34px; border-radius:50%; background:#111827; color:#fff; display:flex; align-items:center;
  justify-content:center; font-size:.78rem; font-weight:600; transition:transform .25s; }
.avatar:hover { transform:scale(1.1) rotate(-4deg); }

/* ---------- cards / KPI ---------- */
[data-testid="stVerticalBlockBorderWrapper"] { background:#FFFFFF; border-radius:14px; border-color:#E5E7EB;
  transition:box-shadow .3s ease, border-color .3s ease; }
[data-testid="stVerticalBlockBorderWrapper"]:hover { box-shadow:0 8px 24px -14px rgba(15,23,42,.25); border-color:#D1D5DB; }
.kpi { background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; padding:16px 18px; min-height:112px;
  position:relative; overflow:hidden; animation:fadeUp .6s cubic-bezier(.22,1,.36,1) both;
  transition:transform .3s cubic-bezier(.22,1,.36,1), box-shadow .3s ease, border-color .3s; }
.kpi::before { content:""; position:absolute; left:0; top:0; height:3px; width:100%; background:#2563EB;
  transform:scaleX(0); transform-origin:left; transition:transform .45s cubic-bezier(.22,1,.36,1); }
.kpi:hover { transform:translateY(-4px); box-shadow:0 14px 28px -16px rgba(15,23,42,.35); border-color:#D1D5DB; }
.kpi:hover::before { transform:scaleX(1); }
.kpi .l { font-size:.72rem; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:.06em; }
.kpi .v { font-size:1.95rem; font-weight:700; color:#111827; line-height:1.25; margin-top:2px; }
.kpi .n { font-size:.78rem; color:#6B7280; }
.num { animation:countup 1.2s cubic-bezier(.22,1,.36,1) both; counter-reset:num var(--n); }
.num::after { content:counter(num); }
.num.pct::after { content:counter(num) "%"; }

/* ---------- pills, tags, feed, profile ---------- */
.pill { display:inline-block; padding:2px 10px; border-radius:999px; font-size:.78rem; font-weight:600; }
.tag { display:inline-block; padding:2px 9px; margin:0 6px 6px 0; border-radius:6px; background:#F3F4F6; color:#374151;
  font-size:.8rem; transition:background .2s, transform .2s; }
.tag:hover { background:#E5E7EB; transform:translateY(-1px); }
.feed { padding:9px 8px; margin:0 -8px; border-bottom:1px solid #F3F4F6; font-size:.9rem; border-radius:8px; transition:background .2s; }
.feed:hover { background:#F9FAFB; }
.feed:last-child { border-bottom:none; }
.colhead { display:flex; justify-content:space-between; align-items:center; font-weight:600; font-size:.9rem;
  padding:6px 4px 8px 4px; border-bottom:2px solid #E5E7EB; margin-bottom:10px; }
.colhead .count { background:#E5E7EB; color:#374151; border-radius:999px; padding:0 8px; font-size:.78rem; }
.colhead i { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; }
.profile h2 { font-size:1.35rem; margin:0; font-weight:700; color:#111827; }
.profile .row { display:flex; padding:7px 0; border-bottom:1px solid #F3F4F6; font-size:.92rem; }
.profile .row .k { width:120px; color:#6B7280; }

/* ---------- buttons ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius:10px; font-weight:500; transition:transform .18s ease, box-shadow .18s ease, background .2s, border-color .2s; }
.stButton > button:hover:not(:disabled), .stDownloadButton > button:hover:not(:disabled),
[data-testid="stFormSubmitButton"] > button:hover:not(:disabled) { transform:translateY(-2px); box-shadow:0 8px 16px -10px rgba(15,23,42,.45); }
.stButton > button:active:not(:disabled) { transform:translateY(0); box-shadow:none; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background:#0F172A; border-right:none; }
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] { padding-bottom:0; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color:#CBD5E1; }
[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.09); margin:1rem 0; }
[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapseButton"] span { color:#94A3B8 !important; }
.sb-brand { display:flex; align-items:center; gap:12px; margin:4px 0 22px 0; animation:slideIn .6s cubic-bezier(.22,1,.36,1) both; }
.sb-logo { width:38px; height:38px; border-radius:11px; background:linear-gradient(135deg,#3B82F6,#1D4ED8); color:#fff;
  display:flex; align-items:center; justify-content:center; font-weight:700; font-size:1.1rem; box-shadow:0 6px 16px -6px rgba(37,99,235,.8);
  transition:transform .4s cubic-bezier(.34,1.56,.64,1); }
.sb-brand:hover .sb-logo { transform:rotate(-8deg) scale(1.08); }
.sb-name { color:#FFFFFF; font-size:1.2rem; font-weight:700; letter-spacing:-.02em; line-height:1.1; }
.sb-sub { color:#64748B; font-size:.74rem; margin-top:2px; }
.sb-label { color:#64748B; font-size:.68rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; margin:0 0 8px 6px; }

[data-testid="stSidebar"] [data-testid="stElementContainer"], [data-testid="stSidebar"] [data-testid="stRadio"] { width:100% !important; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] { gap:4px; width:100%; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div { width:100%; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div { animation:slideIn .55s cubic-bezier(.22,1,.36,1) both; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(1) { animation-delay:.05s; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(2) { animation-delay:.10s; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(3) { animation-delay:.15s; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(4) { animation-delay:.20s; }
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(5) { animation-delay:.25s; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] { position:relative; display:flex; width:100%; box-sizing:border-box; padding:10px 14px; border-radius:10px; cursor:pointer;
  transition:background .25s ease, transform .25s cubic-bezier(.22,1,.36,1); }
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div { display:flex; align-items:center; gap:13px; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child { display:none; }   /* hide radio circle */
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div::before { content:""; width:19px; height:19px; flex:none; background:#94A3B8;
  -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat; -webkit-mask-position:center; mask-position:center;
  -webkit-mask-size:contain; mask-size:contain; transition:background .25s, transform .3s cubic-bezier(.34,1.56,.64,1); }
[data-testid="stSidebar"] [data-testid="stRadioOption"] p { color:#CBD5E1; font-weight:500; font-size:.94rem; margin:0; transition:color .25s; }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover { background:rgba(255,255,255,.07); transform:translateX(4px); }
[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover > div::before { background:#FFFFFF; transform:scale(1.15); }
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] { background:linear-gradient(90deg, rgba(59,130,246,.30), rgba(59,130,246,.06)); }
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p { color:#FFFFFF; font-weight:600; }
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] > div::before { background:#60A5FA; }
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"]::after { content:""; position:absolute; left:0; top:22%; bottom:22%;
  width:3px; border-radius:3px; background:#60A5FA; animation:fadeUp .4s ease both; }

[data-testid="stSidebar"] .stButton > button { background:#2563EB; border:none; color:#FFFFFF; width:100%; padding:.55rem 1rem; }
[data-testid="stSidebar"] .stButton > button p { color:#FFFFFF; font-weight:600; }
[data-testid="stSidebar"] .stButton > button:hover:not(:disabled) { background:#1D4ED8; box-shadow:0 10px 20px -10px rgba(37,99,235,.9); }
.sb-user { display:flex; align-items:center; gap:11px; margin-top:14px; padding:6px 4px; }
.sb-user .av { width:36px; height:36px; border-radius:50%; background:#334155; color:#E2E8F0; display:flex; align-items:center;
  justify-content:center; font-size:.8rem; font-weight:600; }
.sb-user .nm { color:#F1F5F9; font-size:.85rem; font-weight:600; line-height:1.2; }
.sb-user .rl { color:#64748B; font-size:.72rem; }

/* ---------- footer ---------- */
.footer { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-top:3rem; padding:18px 4px 4px 4px;
  border-top:1px solid #E5E7EB; color:#6B7280; font-size:.8rem; }
.footer b { color:#111827; }

@media (prefers-reduced-motion: reduce) { * { animation:none !important; transition:none !important; } }
"""

CSS = "<style>" + BASE + _icon_css() + "</style>"
