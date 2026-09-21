"""Streamlit theme - Material 3 Expressive Dark design system."""

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans+Flex:wght@400;500;600;700;800&display=swap');

/* ==========================================================
   M3 EXPRESSIVE DARK  —  DESIGN TOKEN SYSTEM
   ========================================================== */
:root {
  color-scheme: dark;
  --ui-font: "Google Sans Flex", "Google Sans", "Segoe UI", sans-serif;

  /* Surface elevation roles */
  --md-background:               #0d1117;
  --md-surface:                  #131920;
  --md-surface-container-lowest: #0a0f14;
  --md-surface-container-low:    #141c26;
  --md-surface-container:        #1a2330;
  --md-surface-container-high:   #202c3c;
  --md-surface-container-highest:#283446;

  /* Backward compat aliases */
  --background:        var(--md-background);
  --surface:           var(--md-surface);
  --surface-low:       var(--md-surface-container-low);
  --surface-container: var(--md-surface-container);
  --surface-high:      var(--md-surface-container-high);
  --surface-highest:   var(--md-surface-container-highest);

  /* On-surface */
  --text:             #dde4ee;
  --muted:            #92a1b5;
  --outline:          #3a4758;
  --outline-variant:  #26333f;

  /* Primary  — sky blue, chroma 60 */
  --primary:              #38bdf8;
  --primary-container:    #0c4369;
  --on-primary-container: #d0eeff;
  --primary-dim:          #1e8abf;

  /* Secondary  — emerald green */
  --secondary:              #4ade80;
  --secondary-container:    #143d22;
  --on-secondary-container: #b9f8d0;

  /* Tertiary  — violet */
  --tertiary:              #a78bfa;
  --tertiary-container:    #2e1b5e;
  --on-tertiary-container: #e0d4ff;

  /* Error */
  --error:              #f87171;
  --error-container:    #5c1818;
  --on-error-container: #ffc9c9;

  /* Warning */
  --warning:               #fbbf24;
  --warning-container:     #3d2a07;
  --on-warning-container:  #fed7aa;

  /* Status card surfaces */
  --card-pass:        #0f261a;  --card-pass-border:  #166534;
  --card-fail:        #270e0e;  --card-fail-border:  #991b1b;
  --card-warn:        #271b08;  --card-warn-border:  #854d0e;

  /* Motion curves */
  --spring:     cubic-bezier(0.34, 1.56, 0.64, 1);
  --spring-out: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-std:   cubic-bezier(0.2, 0, 0, 1);
  --dur-quick:  120ms;
  --dur-normal: 250ms;
  --dur-emph:   400ms;

  /* Shape scale */
  --shape-xs:   8px;
  --shape-sm:   12px;
  --shape-md:   16px;
  --shape-lg:   20px;
  --shape-xl:   24px;
  --shape-2xl:  28px;
  --shape-full: 999px;
}

/* ==========================================================
   BASE RESET & APP SHELL
   ========================================================== */
*, *::before, *::after { box-sizing: border-box; }
.stApp,
.stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp label, .stApp input, .stApp textarea, .stApp select,
.stApp li, .stMarkdown,
.sidebar-brand, .sidebar-brand-title, .sidebar-brand-eyebrow, .sidebar-tagline,
.qa-page-header, .qa-page-header h1, .qa-page-eyebrow, .qa-page-caption,
.stCaption, .stButton > button {
  font-family: var(--ui-font) !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button {
  display: none !important;
}
[data-testid="stExpandSidebarButton"] {
  position: relative !important;
  width: 36px !important;
  min-width: 36px !important;
  height: 36px !important;
  overflow: hidden !important;
}
[data-testid="stExpandSidebarButton"] * {
  display: none !important;
}
[data-testid="stExpandSidebarButton"]::before {
  content: "»";
  font-family: var(--ui-font), "Segoe UI", sans-serif !important;
  font-size: 20px !important;
  font-weight: 600 !important;
  color: #c5d4e4 !important;
  line-height: 36px !important;
  display: block !important;
  text-align: center !important;
}
code, pre, kbd, .val-ui, .val-db, .conn-detail {
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace !important;
}
.stApp {
  background: var(--md-background, #0d1117);
  color: var(--text, #dde4ee);
  min-height: 100vh;
}

/* 80% scale on inner content only. Never widen panes — that spilled
   the sidebar over the main page. */
[data-testid="stSidebarUserContent"],
[data-testid="stMainBlockContainer"] {
  zoom: 0.8 !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}

/* 5-layer expressive ambient gradient */
.stApp::before {
  content: ""; position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 90% 55% at 15% -5%,  rgba(56,189,248,0.10), transparent),
    radial-gradient(ellipse 70% 45% at 92% 5%,   rgba(74,222,128,0.07), transparent),
    radial-gradient(ellipse 55% 35% at 50% 105%, rgba(167,139,250,0.06), transparent),
    radial-gradient(ellipse 40% 60% at 85% 70%,  rgba(56,189,248,0.04), transparent),
    radial-gradient(ellipse 60% 30% at 5%  75%,  rgba(74,222,128,0.03), transparent);
  pointer-events: none; z-index: -1;
}

header[data-testid="stHeader"] {
  background: transparent !important;
  box-shadow: none !important;
}


/* ==========================================================
   SIDEBAR
   ========================================================== */
[data-testid="stSidebar"] {
  background: rgba(10,15,20,0.95) !important;
  border-right: 1px solid var(--outline) !important;
  box-shadow: 8px 0 32px rgba(0,0,0,0.35);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  overflow: hidden !important;
  transform: none !important;
  zoom: 1 !important;
}
[data-testid="stSidebar"] hr { border-color: var(--outline-variant, #26333f) !important; margin: 12px 0 !important; }

/* Remove top gap while preserving collapse button */
[data-testid="stSidebar"] { position: relative !important; }
[data-testid="stSidebar"] > div:first-child { padding-top:0 !important; margin-top:0 !important; }
[data-testid="stSidebar"] > div > div:first-child { padding-top:0 !important; margin-top:0 !important; }
[data-testid="stSidebarContent"] { position: relative !important; padding-top: 1.75rem !important; margin-top:0 !important; }
[data-testid="stSidebarUserContent"] { padding-top: 0.35rem !important; }
[data-testid="stSidebar"] > div > div > div:first-child { margin-top:0 !important; padding-top:0 !important; }

[data-testid="stSidebarHeader"] {
  position: static !important;
  height: 0 !important;
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  overflow: visible !important;
  border: none !important;
}

.sidebar-brand { display:flex; align-items:center; gap:12px; margin-top:8px; margin-bottom:6px; width:max-content; max-width:100%; }
.sidebar-collapse-slot {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  margin-left: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  color: #c5d4e4;
  font-size: 20px;
  font-weight: 600;
  line-height: 1;
  user-select: none;
}
.sidebar-collapse-slot::before { content: "«"; }
.sidebar-collapse-slot:hover { background: rgba(125, 211, 252, 0.12); color: #f5fbff; }
.sidebar-brand-icon {
  width:44px; height:44px; border-radius:18px;
  display:flex; align-items:center; justify-content:center;
  font-size:13px; font-weight:800; letter-spacing:0.04em;
  color:var(--on-primary-container);
  background:linear-gradient(145deg, #0e5080, #052035);
  border:1px solid rgba(56,189,248,0.40);
  box-shadow:0 0 20px rgba(56,189,248,0.15), 0 8px 20px rgba(0,0,0,0.3);
}
.sidebar-brand-eyebrow { color:var(--primary); font-size:10px; font-weight:700; letter-spacing:0.16em; text-transform:uppercase; }
.sidebar-brand-title { color:var(--text); font-size:20px; font-weight:700; line-height:1.1; }
.sidebar-tagline { color:var(--muted); font-size:12px; line-height:1.45; margin-bottom:18px; padding-bottom:14px; border-bottom:1px solid var(--outline-variant); }
.sidebar-footer { margin-top:16px; padding-top:12px; border-top:1px solid var(--outline-variant,#26333f); color:var(--muted,#92a1b5); font-size:11px; text-align:center; }

.sb-group-label, .sidebar-section-label {
  color: var(--muted, #92a1b5); font-size: 11px; font-weight: 700;
  letter-spacing: 0.12em; text-transform: uppercase;
  margin: 14px 4px 6px;
}

.sidebar-status-card {
  background: var(--md-surface-container, #1a2330);
  border: 1px solid var(--outline-variant, #26333f);
  border-radius: 14px; padding: 10px 12px; margin: 8px 0 12px;
}
.sidebar-status-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; font-size: 12px; color: var(--muted, #92a1b5); padding: 4px 0;
}
.sidebar-status-row code {
  background: var(--md-surface-container-high, #202c3c); color: #38bdf8;
  border-radius: 6px; padding: 2px 6px; font-size: 11px;
}
.sidebar-status-row strong { color: var(--text, #dde4ee); font-weight: 600; }

.sidebar-steps { display: flex; flex-direction: column; gap: 6px; margin: 4px 0 14px; }
.sidebar-step {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 12px;
  border: 1px solid transparent; font-size: 12px;
}
.sidebar-step.done { background: rgba(20,83,45,0.25); border-color: rgba(22,101,52,0.45); color: #86efac; }
.sidebar-step.active { background: rgba(12,74,110,0.45); border-color: rgba(125,211,252,0.35); color: #d0eeff; }
.sidebar-step.pending { background: #1a2330; border-color: #26333f; color: #92a1b5; }
.sidebar-step-dot {
  width: 22px; height: 22px; border-radius: 999px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; background: rgba(255,255,255,0.06); flex-shrink: 0;
}
.sidebar-step-label { font-weight: 600; }

[data-testid="stSidebarNav"] { display:none !important; }

/* ==========================================================
   LAYOUT & TYPOGRAPHY
   ========================================================== */
.block-container { padding-top:1.25rem !important; padding-bottom:3.5rem !important; max-width:1300px !important; }

h1 { font-size:clamp(26px,3.2vw,38px) !important; font-weight:800 !important; color:var(--text, #dde4ee) !important; line-height:1.15 !important; }
h2 { font-size:clamp(20px,2.4vw,28px) !important; font-weight:700 !important; color:var(--text, #dde4ee) !important; }
h3 { font-size:18px !important; font-weight:650 !important; color:var(--text) !important; }
h4, h5, h6 { color:var(--text) !important; font-weight:600 !important; }
p, li, .stMarkdown { color:var(--text); line-height:1.65; }
label { color:var(--text) !important; font-size:13px !important; font-weight:500 !important; }
.stCaption, small, .qa-page-caption {
  color: var(--muted, #92a1b5) !important;
  font-family: var(--ui-font) !important;
  font-size: 15px !important;
  font-weight: 400 !important;
  line-height: 1.55 !important;
}

.qa-page-eyebrow {
  color:var(--primary); font-size:11px; font-weight:700; letter-spacing:0.16em;
  text-transform:uppercase; margin-bottom:6px; display:flex; align-items:center; gap:8px;
}
.qa-page-eyebrow::before { content:""; display:inline-block; width:18px; height:3px; background:var(--primary); border-radius:99px; }
.qa-page-header { margin-bottom:1.5rem; padding-bottom:1rem; border-bottom:1px solid var(--outline-variant); }
.qa-page-header h1 {
  margin:0 !important;
  color: var(--text, #dde4ee) !important;
}
.section-title { font-size:18px; font-weight:600; color:var(--text); margin:36px 0 16px; display:flex; align-items:center; justify-content:space-between; gap:12px; padding:0 4px; }
.section-badge { font-size:12px; font-weight:600; padding:5px 14px; border-radius:var(--shape-full); background:var(--md-surface-container-high); color:var(--primary); border:1px solid var(--outline-variant); white-space:nowrap; }
.timestamp { color:var(--muted); font-size:13px; }
.empty-state { padding:48px; text-align:center; color:var(--muted); font-size:14px; }

/* ==========================================================
   METRICS (st.metric)
   ========================================================== */
div[data-testid="stMetric"] {
  background:var(--md-surface-container); border:1px solid var(--outline-variant);
  border-left:3px solid var(--primary); border-radius:var(--shape-2xl);
  padding:20px 22px 18px; position:relative; overflow:visible;
  min-width: 0;
  transition:transform var(--dur-normal) var(--spring), box-shadow var(--dur-normal) var(--ease-std);
}
div[data-testid="stMetric"]:hover { transform:translateY(-3px); box-shadow:0 10px 32px rgba(0,0,0,0.4); }
div[data-testid="stMetricLabel"] > div,
div[data-testid="stMetricLabel"] p { font-size:11px !important; font-weight:600 !important; text-transform:uppercase !important; letter-spacing:0.08em !important; color:var(--muted) !important; white-space: normal !important; }
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] > div,
div[data-testid="stMetricValue"] p {
  font-size: clamp(15px, 1.8vw, 28px) !important;
  font-weight: 800 !important;
  line-height: 1.25 !important;
  color: var(--text) !important;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  overflow-wrap: anywhere !important;
  word-break: break-word !important;
}
div[data-testid="stMetricDelta"] { color:var(--secondary) !important; font-size:13px !important; }

/* Summary cards */
.summary-card {
  background:var(--md-surface-container); border:1px solid var(--outline-variant);
  border-left:3px solid var(--primary); border-radius:var(--shape-2xl);
  padding:16px 14px; position:relative; overflow:hidden; min-width:0; max-width:100%;
  box-sizing: border-box;
  transition:transform var(--dur-normal) var(--spring), box-shadow var(--dur-normal) var(--ease-std);
}
.summary-card::after { content:""; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,var(--primary),transparent); opacity:0; transition:opacity var(--dur-normal) var(--ease-std); }
.summary-card:hover { transform:translateY(-3px); box-shadow:0 10px 32px rgba(0,0,0,0.4); }
.summary-card:hover::after { opacity:1; }
.summary-card .title { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:10px; }
.summary-card .value { font-size:32px; font-weight:800; line-height:1.25; color:var(--text); overflow-wrap:anywhere; word-break:break-word; white-space:normal; }
.summary-card .value.compact { font-size:12px; font-weight:600; line-height:1.4; }
.summary-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:14px; margin-bottom:28px; width:100%; max-width:100%; }
.summary-grid.equal-cards {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: stretch;
  overflow: hidden;
}
.summary-grid.equal-cards .summary-card {
  min-height: 112px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-width: 100%;
}
.summary-grid.equal-cards .value {
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
  max-width: 100%;
  overflow-wrap: anywhere;
  word-break: break-all;
}
.summary-card.pass, .summary-card.card-pass { background:var(--card-pass); border-color:var(--card-pass-border); border-left-color:var(--secondary); }
.summary-card.fail, .summary-card.card-fail { background:var(--card-fail); border-color:var(--card-fail-border); border-left-color:var(--error); }
.summary-card.warn, .summary-card.card-warn { background:var(--card-warn); border-color:var(--card-warn-border); border-left-color:var(--warning); }
.summary-card.pass .value, .summary-card.card-pass .value { color:var(--secondary); }
.summary-card.fail .value, .summary-card.card-fail .value { color:var(--error); }
.summary-card.warn .value, .summary-card.card-warn .value { color:var(--warning); }

/* ==========================================================
   BUTTONS — M3 Expressive variant system
   ========================================================== */
.stButton > button {
  background:var(--md-surface-container-high, #202c3c) !important;
  color:#d0eeff !important;
  border:1px solid var(--outline, #3a4758) !important; border-radius:var(--shape-lg) !important;
  font-size:13px !important; font-weight:600 !important; padding:9px 22px !important;
}
.stButton > button:hover { background:var(--md-surface-container-highest) !important; border-color:var(--primary) !important; border-radius:var(--shape-xl) !important; color:var(--text) !important; box-shadow:0 0 0 2px rgba(56,189,248,0.15) !important; }
.stButton > button:active { transform:scale(0.97) !important; }
.stButton > button:focus-visible { outline:2px solid var(--primary) !important; outline-offset:2px !important; }

.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
  background:#0b4f7a !important;
  border-color:#38bdf8 !important;
  color:#f5fbff !important;
  box-shadow:0 2px 12px rgba(3,105,161,0.35) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
  background:#0a5f96 !important;
  color:#ffffff !important;
}

/* Sidebar nav: Import-page button colors, rounded-rect (not pill) */
[data-testid="stSidebar"] [data-testid="stButton"] {
  margin: 6px 0 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button,
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
[data-testid="stSidebar"] button[data-testid="baseButton-secondary"],
[data-testid="stSidebar"] button[data-testid="baseButton-primary"],
[data-testid="stSidebar"] button[kind="secondary"],
[data-testid="stSidebar"] button[kind="primary"] {
  width: 100% !important;
  min-height: 46px !important;
  height: 46px !important;
  padding: 12px 20px !important;
  border-radius: 12px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  letter-spacing: 0 !important;
  text-align: center !important;
  justify-content: center !important;
  align-items: center !important;
  background: #1a2836 !important;
  border: 1px solid #4a6d88 !important;
  color: #d7e6f3 !important;
  box-shadow: none !important;
  line-height: 1.2 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button p,
[data-testid="stSidebar"] button[data-testid^="stBaseButton"] p,
[data-testid="stSidebar"] button[kind] p {
  font-size: 14px !important;
  font-weight: 600 !important;
  color: inherit !important;
  margin: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover,
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stSidebar"] button[kind="secondary"]:hover {
  background: #223445 !important;
  border-color: #6b8aa6 !important;
  border-radius: 12px !important;
  color: #ffffff !important;
  box-shadow: none !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
[data-testid="stSidebar"] button[data-testid="baseButton-primary"],
[data-testid="stSidebar"] button[kind="primary"] {
  background: #0c6f9e !important;
  border: 1px solid #1aa3d6 !important;
  color: #f5fbff !important;
  font-weight: 700 !important;
  box-shadow: 0 2px 10px rgba(12, 111, 158, 0.35) !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] p,
[data-testid="stSidebar"] button[kind="primary"] p {
  font-weight: 700 !important;
  color: #f5fbff !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover,
[data-testid="stSidebar"] button[kind="primary"]:hover {
  background: #0d7fb3 !important;
  border-color: #38bdf8 !important;
  border-radius: 12px !important;
  color: #ffffff !important;
}

.stDownloadButton > button {
  background:var(--md-surface-container) !important; color:var(--text) !important;
  border:1px solid var(--outline-variant) !important; border-radius:var(--shape-lg) !important;
  font-size:13px !important; font-weight:500 !important; padding:8px 18px !important;
  transition:background var(--dur-quick) var(--ease-std), border-radius var(--dur-normal) var(--spring) !important;
}
.stDownloadButton > button:hover { background:var(--md-surface-container-high) !important; border-color:var(--secondary) !important; border-radius:var(--shape-xl) !important; box-shadow:0 0 0 2px rgba(74,222,128,0.15) !important; }

/* ==========================================================
   FORM ELEMENTS — M3 Outlined field
   ========================================================== */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
  background:var(--md-surface-container-low) !important; color:var(--text) !important;
  border:1.5px solid var(--outline) !important; border-radius:var(--shape-md) !important;
  padding:10px 14px !important; font-size:14px !important;
  transition:border-color var(--dur-quick) var(--ease-std), box-shadow var(--dur-quick) var(--ease-std), border-radius var(--dur-normal) var(--spring) !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
  border-color:var(--primary) !important; border-width:2px !important;
  border-radius:var(--shape-lg) !important; box-shadow:0 0 0 3px rgba(56,189,248,0.12) !important; outline:none !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color:var(--muted) !important; opacity:0.7 !important; }

.stSelectbox [data-baseweb="select"] > div, [data-baseweb="select"] > div {
  background:var(--md-surface-container-low) !important; border:1.5px solid var(--outline) !important;
  border-radius:var(--shape-md) !important; color:var(--text) !important;
}
[data-baseweb="select"] > div:focus-within { border-color:var(--primary) !important; border-width:2px !important; box-shadow:0 0 0 3px rgba(56,189,248,0.12) !important; }
[data-baseweb="menu"] { background:var(--md-surface-container-highest) !important; border:1px solid var(--outline-variant) !important; border-radius:var(--shape-md) !important; box-shadow:0 8px 32px rgba(0,0,0,0.5) !important; backdrop-filter:blur(16px) !important; }
[data-baseweb="option"]:hover { background:var(--md-surface-container-high) !important; border-radius:var(--shape-sm) !important; }
[aria-selected="true"][data-baseweb="option"] { background:var(--primary-container) !important; color:var(--on-primary-container) !important; border-radius:var(--shape-sm) !important; }

.stRadio label { background:var(--md-surface-container) !important; border:1px solid var(--outline-variant) !important; border-radius:var(--shape-md) !important; padding:9px 14px !important; margin:0 0 4px !important; transition:background var(--dur-quick) var(--ease-std), border-radius var(--dur-normal) var(--spring), border-color var(--dur-quick) var(--ease-std) !important; }
.stRadio label:hover { background:var(--md-surface-container-high) !important; border-color:var(--outline) !important; border-radius:var(--shape-lg) !important; }
.stRadio [aria-checked="true"] label, .stRadio label[data-checked="true"] { background:var(--primary-container) !important; border-color:var(--primary) !important; border-radius:var(--shape-lg) !important; color:var(--on-primary-container) !important; box-shadow:0 0 0 1px rgba(56,189,248,0.2) !important; }
.stRadio label > div:first-child { display:none !important; }
.stRadio > div { gap:4px !important; background:transparent !important; border:none !important; }
.stCheckbox label { color:var(--text) !important; font-size:13px !important; gap:10px !important; }

[data-testid="stFileUploader"] { background:var(--md-surface-container-low) !important; border:2px dashed var(--outline) !important; border-radius:var(--shape-xl) !important; padding:24px !important; transition:border-color var(--dur-quick) var(--ease-std), background var(--dur-quick) var(--ease-std) !important; }
[data-testid="stFileUploader"]:hover { border-color:var(--primary) !important; background:rgba(56,189,248,0.04) !important; }

/* ==========================================================
   TABS — M3 secondary tab with animated underline
   ========================================================== */
.stTabs [data-baseweb="tab-list"],
[data-testid="stTabs"] [role="tablist"] {
  gap: 10px !important;
  background: transparent !important;
  border-bottom: 1px solid var(--outline-variant) !important;
  padding: 0 !important;
}
.stTabs [data-baseweb="tab"],
.stTabs button[role="tab"],
[data-testid="stTab"],
[data-testid="stTabs"] button[role="tab"] {
  background: transparent !important;
  border: none !important;
  border-radius: var(--shape-md) var(--shape-md) 0 0 !important;
  color: var(--muted) !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  padding: 10px 28px !important;
  margin: 0 4px !important;
  position: relative !important;
}
.stTabs [data-baseweb="tab"] p,
.stTabs button[role="tab"] p,
[data-testid="stTab"] p {
  margin: 0 !important;
  padding: 0 4px !important;
}
.stTabs [data-baseweb="tab"]::after,
.stTabs button[role="tab"]::after,
[data-testid="stTab"]::after {
  content: "";
  position: absolute;
  bottom: -1px;
  left: 16px;
  right: 16px;
  height: 2px;
  background: var(--primary);
  border-radius: 99px;
  transform: scaleX(0);
}
.stTabs [data-baseweb="tab"]:hover,
.stTabs button[role="tab"]:hover,
[data-testid="stTab"]:hover {
  background: rgba(56,189,248,0.06) !important;
  color: var(--text) !important;
}
.stTabs [aria-selected="true"],
[data-testid="stTab"][aria-selected="true"] {
  color: var(--primary) !important;
  background: rgba(56,189,248,0.08) !important;
}
.stTabs [aria-selected="true"]::after,
[data-testid="stTab"][aria-selected="true"]::after { transform: scaleX(1); }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem !important; }

/* Expanders */
.stExpander { background:var(--md-surface-container) !important; border:1px solid var(--outline-variant) !important; border-radius:var(--shape-xl) !important; overflow:hidden !important; transition:border-color var(--dur-quick) var(--ease-std) !important; }
.stExpander:hover { border-color:var(--outline) !important; }
.stExpander > details > summary { background:var(--md-surface-container) !important; padding:14px 18px !important; font-weight:600 !important; color:var(--text) !important; font-size:14px !important; }
.stExpander > details > summary:hover { background:var(--md-surface-container-high) !important; }
.stExpander > details[open] > summary { border-bottom:1px solid var(--outline-variant) !important; }

/* DataFrames */
.stDataFrame, [data-testid="stDataFrame"] { border:1px solid var(--outline-variant) !important; border-radius:var(--shape-2xl) !important; overflow:hidden !important; box-shadow:0 4px 24px rgba(0,0,0,0.25) !important; }

/* Dividers */
hr { border:none !important; border-top:1px solid var(--outline-variant) !important; margin:1.5rem 0 !important; }

/* Progress bars */
.stProgress > div > div > div { background:linear-gradient(90deg,var(--primary),var(--tertiary)) !important; border-radius:999px !important; }
.stProgress > div > div { background:var(--md-surface-container-high) !important; border-radius:999px !important; }

/* Loading state */
@keyframes qa-loader-spin {
  to { transform: rotate(360deg); }
}

@keyframes qa-loader-pulse {
  0%, 100% { opacity: 0.58; transform: scale(0.96); }
  50% { opacity: 1; transform: scale(1); }
}

.stSpinner {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  color: var(--on-primary-container) !important;
  font-size: 0.84rem !important;
  font-weight: 600 !important;
}

.stSpinner > div {
  width: 1.35rem !important;
  height: 1.35rem !important;
  border: 3px solid rgba(168, 200, 255, 0.2) !important;
  border-top-color: var(--primary) !important;
  border-right-color: var(--tertiary) !important;
  border-radius: 50% !important;
  animation: qa-loader-spin 0.8s linear infinite, qa-loader-pulse 1.5s ease-in-out infinite !important;
  filter: drop-shadow(0 0 7px rgba(168, 200, 255, 0.35));
}

/* Scrollbar */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:var(--md-surface-container); }
::-webkit-scrollbar-thumb { background:var(--outline); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:var(--primary); }

/* ==========================================================
   ALERTS / FEEDBACK
   ========================================================== */
.stAlert { border-radius:var(--shape-lg) !important; font-size:13px !important; }
div[data-baseweb="notification"] { border-radius:var(--shape-lg) !important; }

/* Success */
div[data-testid="stAlert"][data-type="success"],
.element-container:has([data-type="success"]) > div { background:var(--secondary-container) !important; border:1px solid rgba(74,222,128,0.4) !important; border-left:3px solid var(--secondary) !important; color:var(--on-secondary-container) !important; }
/* Error */
div[data-testid="stAlert"][data-type="error"],
.element-container:has([data-type="error"]) > div { background:var(--error-container) !important; border:1px solid rgba(248,113,113,0.4) !important; border-left:3px solid var(--error) !important; color:var(--on-error-container) !important; }
/* Warning */
div[data-testid="stAlert"][data-type="warning"],
.element-container:has([data-type="warning"]) > div { background:var(--warning-container) !important; border:1px solid rgba(251,191,36,0.4) !important; border-left:3px solid var(--warning) !important; color:var(--on-warning-container) !important; }
/* Info */
div[data-testid="stAlert"][data-type="info"],
.element-container:has([data-type="info"]) > div { background:var(--primary-container) !important; border:1px solid rgba(56,189,248,0.35) !important; border-left:3px solid var(--primary) !important; color:var(--on-primary-container) !important; }

/* Badges */
.badge { display:inline-flex; align-items:center; justify-content:center; padding:4px 12px; border-radius:var(--shape-full); font-size:11px; font-weight:700; letter-spacing:0.04em; text-transform:uppercase; white-space:nowrap; }
.badge-PASS          { background:#0f261a; color:var(--secondary);  border:1px solid #166534; }
.badge-FAIL          { background:#270e0e; color:var(--error);       border:1px solid #991b1b; }
.badge-NOT_COMPARABLE{ background:var(--warning-container); color:var(--warning); border:1px solid #a16207; }
.badge-MISSING       { background:#2a1800; color:#fdba74; border:1px solid #9a3412; }
.badge-SKIPPED       { background:#1f1a00; color:#fde047; border:1px solid #78350f; }
.badge-NOT_SHOWN     { background:var(--primary-container); color:var(--primary); border:1px solid #1e40af; }
.badge-PENDING       { background:var(--md-surface-container-high); color:var(--muted); border:1px solid var(--outline); }

/* Pills */
.pill { display:inline-flex; align-items:center; padding:6px 16px; border-radius:var(--shape-full); font-size:12px; font-weight:500; cursor:pointer; user-select:none; border:1px solid var(--outline-variant); background:var(--md-surface-container-high); color:var(--muted); transition:background var(--dur-quick) var(--ease-std), color var(--dur-quick) var(--ease-std); }
.pill:hover { background:var(--md-surface-container-highest); color:var(--text); }
.pill.active { background:var(--primary-container); color:var(--on-primary-container); border-color:var(--primary); }

/* ==========================================================
   TABLE CONTAINERS & MISC
   ========================================================== */
.controls-bar { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:16px; margin-bottom:20px; background:var(--md-surface-container-low); border:1px solid var(--outline-variant); border-radius:var(--shape-xl); padding:14px 20px; }
.controls { display:flex; flex-wrap:wrap; gap:12px; margin-bottom:28px; align-items:center; }
.table-container { overflow: auto; margin-bottom: 36px; background: var(--md-surface-container); border: 1px solid var(--outline-variant); border-radius: var(--shape-2xl); box-shadow: 0 4px 24px rgba(0,0,0,0.22); }
.table-container table { width:100%; border-collapse:separate; border-spacing:0; margin:0; border:none; font-size:13px; }
.table-container th { background:var(--md-surface-container-high); color:var(--muted); font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.07em; padding:14px 18px; border-bottom:1px solid var(--outline-variant); white-space:nowrap; }
.table-container td { padding:13px 18px; font-size:13px; border-bottom:1px solid var(--outline-variant); color:var(--text); }
.table-container tr:last-child td { border-bottom:none; }
.table-container tr.main-row:hover td { background:var(--md-surface-container-high); }
.toggle-btn { font-size:11px; padding:4px 12px; border-radius:var(--shape-full); border:1px solid var(--outline-variant); background:var(--md-surface-container-high); color:var(--primary); cursor:pointer; font-weight:600; transition:background var(--dur-quick) var(--ease-std), border-color var(--dur-quick) var(--ease-std), border-radius var(--dur-normal) var(--spring); }
.toggle-btn:hover { background:var(--md-surface-container-highest); border-color:var(--primary); border-radius:var(--shape-sm); }
.export-btn, .btn-export { padding:7px 18px; background:var(--primary-container); border:1px solid var(--primary); border-radius:var(--shape-full); color:var(--on-primary-container); font-size:12px; font-weight:600; cursor:pointer; transition:opacity 0.2s, box-shadow 0.2s; }
.export-btn:hover, .btn-export:hover { opacity:0.9; box-shadow:0 4px 16px rgba(56,189,248,0.25); }
.detail-row > td { background:var(--md-surface-container-lowest) !important; padding:16px 20px !important; }
.detail-table-scroll { overflow-x:auto; border:1px solid var(--outline-variant); border-radius:var(--shape-md); }
.detail-table { margin:0 !important; border:none !important; border-radius:0 !important; border-collapse:collapse !important; }
.detail-table th, .detail-table td { padding:8px 12px !important; border-bottom:1px solid var(--outline-variant); white-space:nowrap; font-size:12px; }
.detail-table th { background:var(--md-surface-container-high) !important; color:var(--muted); }
.import-action-gap {
  height: 1.5rem;
  width: 100%;
}
.kpi-actions:empty { display:none; }
.query-panel-header { margin-bottom:6px; font-size:12px; color:var(--muted); font-weight:600; }
.val-ui  { font-family:monospace; font-weight:600; color:#67e8f9; }
.val-db  { font-family:monospace; font-weight:600; color:#fdba74; }
.val-muted { color:var(--muted); opacity:0.6; }
.query-box { background:var(--md-surface-container); border:1px solid var(--outline-variant); border-radius:var(--shape-md); }
.query-box pre { margin:0; padding:12px 40px 12px 12px; color:var(--primary); font-size:12px; overflow-x:auto; white-space:pre-wrap; }

/* ==========================================================
   STORY CARDS  (HTML <details>)
   ========================================================== */
.story-card-wrap { background:var(--md-surface-container); border:1px solid var(--outline-variant); border-radius:var(--shape-xl); margin-bottom:16px; overflow:hidden; transition:border-color var(--dur-quick) var(--ease-std), box-shadow var(--dur-quick) var(--ease-std); }
.story-card-wrap:hover { border-color:var(--outline); box-shadow:0 4px 20px rgba(0,0,0,0.3); }
.story-card-summary { display:flex; align-items:center; gap:12px; padding:13px 16px; cursor:pointer; list-style:none; transition:background var(--dur-quick) var(--ease-std); }
.story-card-summary:hover { background:var(--md-surface-container-high); }
.story-card-id { font-size:11px; font-weight:700; padding:3px 9px; border-radius:var(--shape-full); background:var(--primary-container); color:var(--primary); white-space:nowrap; flex-shrink:0; }
.story-card-title { font-size:13px; font-weight:600; color:var(--text); flex:1; }
.story-card-badge { font-size:11px; font-weight:600; padding:3px 10px; border-radius:var(--shape-full); border:1px solid var(--outline-variant); color:var(--muted); white-space:nowrap; flex-shrink:0; }
.story-card-chevron { width:18px; height:18px; flex-shrink:0; color:var(--muted); transition:transform var(--dur-normal) var(--spring); }
details.story-card-wrap[open] .story-card-chevron { transform:rotate(180deg); }
.story-card-body { padding:16px 18px; border-top:1px solid var(--outline-variant); background:var(--md-surface-container-low); }
.story-card-section-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--primary); margin:12px 0 6px; }
.story-card-section-label:first-child { margin-top:0; }
.story-card-text { font-size:13px; color:var(--text); line-height:1.6; }
div[class*="st-key-remove_ado_story"] {
  padding-top: 8px;
  display: flex;
  justify-content: center;
}
div[class*="st-key-remove_ado_story"] button {
  min-width: 2.25rem;
  height: 2.25rem;
  padding: 0 !important;
  border-radius: 999px;
  border: 1px solid var(--outline-variant);
  background: var(--md-surface-container-high);
  color: var(--muted);
  font-size: 16px;
  line-height: 1;
}
div[class*="st-key-remove_ado_story"] button:hover {
  border-color: #f87171;
  color: #f87171;
  background: rgba(248, 113, 113, 0.12);
}

/* ==========================================================
   PAGE LOADER — shown while Streamlit is running / navigating
   ========================================================== */
.qa-page-loader {
  position: fixed;
  inset: 0;
  z-index: 99990;
  display: none;
  align-items: center;
  justify-content: center;
  background: rgba(8, 12, 18, 0.78);
  backdrop-filter: blur(12px) saturate(140%);
  -webkit-backdrop-filter: blur(12px) saturate(140%);
  pointer-events: none;
}
body:has([data-testid="stApp"][data-test-script-state="running"]) #qa-page-loader,
body:has([data-testid="stApp"][data-test-script-state="rerunRequested"]) #qa-page-loader,
body:has([data-testid="stApp"][data-test-script-state="initial"]) #qa-page-loader {
  display: flex !important;
}
.qa-loader-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 28px 36px;
  border-radius: 20px;
  background: rgba(26, 35, 48, 0.92);
  border: 1px solid #3a4758;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(56, 189, 248, 0.12);
}
.qa-loader-ring {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 3px solid rgba(56, 189, 248, 0.18);
  border-top-color: #38bdf8;
  border-right-color: #4ade80;
  animation: qa-spin 0.75s linear infinite;
}
.qa-loader-text {
  font-family: var(--ui-font), "Segoe UI", sans-serif;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #d0eeff;
}
@keyframes qa-spin {
  to { transform: rotate(360deg); }
}
header[data-testid="stHeader"] { z-index: 100000 !important; }

/* Hide Streamlit chrome */
#MainMenu { visibility:hidden; }
footer    { visibility:hidden; }
iframe[height="0"] {
  position: absolute !important;
  width: 0 !important;
  height: 0 !important;
  border: 0 !important;
  visibility: hidden !important;
}

</style>
"""


def apply_theme() -> None:
    import streamlit as st
    import streamlit.components.v1 as components

    st.markdown(THEME_CSS, unsafe_allow_html=True)
    components.html(
        """
<script>
(function () {
  const doc = window.parent.document;
  if (!doc.getElementById("qa-page-loader")) {
    const el = doc.createElement("div");
    el.id = "qa-page-loader";
    el.className = "qa-page-loader";
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", "polite");
    el.setAttribute("aria-label", "Loading");
    el.innerHTML = '<div class="qa-loader-card"><div class="qa-loader-ring"></div><div class="qa-loader-text">Loading</div></div>';
    doc.body.appendChild(el);
  }
  if (doc.__qaCollapseBound) return;
  doc.__qaCollapseBound = true;
  doc.addEventListener("click", (event) => {
    const slot = event.target && event.target.closest
      ? event.target.closest(".sidebar-collapse-slot")
      : null;
    if (!slot) return;
    const native = doc.querySelector("[data-testid='stSidebarCollapseButton'] button")
      || doc.querySelector("[data-testid='stSidebarCollapseButton']");
    if (native) native.click();
  });
})();
</script>
""",
        height=0,
        width=0,
    )


def page_header(title: str, caption: str = "", eyebrow: str = "QA Accelerator") -> None:
    import html as html_mod
    import streamlit as st
    st.markdown(
        f'<div class="qa-page-eyebrow">{html_mod.escape(eyebrow)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="qa-page-header"><h1 style="margin:0;">{html_mod.escape(title)}</h1></div>',
        unsafe_allow_html=True,
    )
    if caption:
        st.markdown(
            f'<p class="qa-page-caption">{html_mod.escape(caption)}</p>',
            unsafe_allow_html=True,
        )
