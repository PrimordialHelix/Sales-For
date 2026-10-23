"""Reusable visual theme for the SALESCAST Streamlit dashboard."""

SALESCAST_CSS = r"""
<style>
  :root {
    color-scheme: dark;
    --sc-bg: #0b1220;
    --sc-surface: #111827;
    --sc-card: #172033;
    --sc-border: #293548;
    --sc-text: #f8fafc;
    --sc-muted: #94a3b8;
    --sc-teal: #2dd4bf;
    --sc-purple: #8b5cf6;
    --sc-emerald: #10b981;
    --sc-blue: #60a5fa;
    --sc-pink: #e84393;
  }

  html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  .stApp {
    color: var(--sc-text);
    background:
      radial-gradient(ellipse at 78% -10%, rgba(45, 212, 191, .08), transparent 38%),
      radial-gradient(ellipse at 5% 15%, rgba(139, 92, 246, .08), transparent 32%),
      var(--sc-bg);
  }
  [data-testid="stHeader"] { background: transparent; }
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101827 0%, #0d1421 100%);
    border-right: 1px solid rgba(148, 163, 184, .12);
  }
  [data-testid="stSidebar"] > div:first-child { background: transparent; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--sc-muted); }
  [data-testid="stSidebar"] [data-testid="stRadio"] label {
    border: 1px solid transparent;
    border-radius: 10px;
    padding: .2rem .5rem;
    transition: background-color .18s ease, border-color .18s ease, color .18s ease;
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(45, 212, 191, .07);
    border-color: rgba(45, 212, 191, .2);
  }
  [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(45, 212, 191, .13), rgba(139, 92, 246, .08));
    border-color: rgba(45, 212, 191, .28);
    color: var(--sc-text);
  }

  .block-container {
    max-width: 1480px;
    padding-top: 2rem;
    padding-bottom: 3.5rem;
  }
  h1, h2, h3 { color: var(--sc-text); letter-spacing: -.025em; }
  [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] li { color: #cbd5e1; }
  [data-testid="stCaptionContainer"] { color: var(--sc-muted); }
  hr { border-color: rgba(148, 163, 184, .14); }

  .salescast-brand {
    display: flex;
    align-items: center;
    gap: .7rem;
    margin: .15rem 0 1.1rem;
  }
  .salescast-brand-mark {
    display: block;
    flex: 0 0 auto;
    width: 2.45rem;
    height: 2.45rem;
    border-radius: 15px;
    filter: drop-shadow(0 0 9px rgba(45, 212, 191, .12));
    animation: logo-arrive .7s cubic-bezier(.2,.7,.2,1) both,
      logo-breathe 5.5s ease-in-out .7s infinite;
  }
  .salescast-brand:hover .salescast-brand-mark {
    filter: drop-shadow(0 0 15px rgba(45, 212, 191, .32));
  }
  .salescast-hero-wordmark {
    display: block;
    width: min(268px, 75%);
    height: auto;
    margin: 0 0 .65rem -.35rem;
    filter: drop-shadow(0 0 18px rgba(45, 212, 191, .08));
  }
  .salescast-brand-name {
    color: var(--sc-text);
    font-size: 1.05rem;
    font-weight: 750;
    letter-spacing: .12em;
  }
  .salescast-brand-subtitle {
    margin-top: .12rem;
    color: var(--sc-muted);
    font-size: .72rem;
    letter-spacing: .02em;
  }

  .salescast-hero {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    margin: .1rem 0 1.5rem;
    padding: clamp(1.5rem, 4vw, 2.75rem);
    border: 1px solid rgba(45, 212, 191, .2);
    border-radius: 22px;
    background:
      radial-gradient(ellipse at 78% 22%, rgba(45, 212, 191, .15), transparent 40%),
      radial-gradient(ellipse at 8% 100%, rgba(139, 92, 246, .18), transparent 42%),
      linear-gradient(135deg, rgba(17, 24, 39, .96), rgba(15, 23, 42, .88));
    box-shadow: 0 18px 60px rgba(0, 0, 0, .2);
  }
  [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(45, 212, 191, .19);
    border-radius: 20px;
    background:
      radial-gradient(ellipse at 50% 15%, rgba(45, 212, 191, .1), transparent 60%),
      rgba(17, 24, 39, .76);
    box-shadow: inset 0 1px rgba(248, 250, 252, .025), 0 12px 35px rgba(0, 0, 0, .16);
  }
  [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] {
    text-align: center;
    letter-spacing: .08em;
    text-transform: uppercase;
  }
  iframe[title="streamlit_lottie.streamlit_lottie"] {
    height: 160px !important;
    background: var(--sc-bg);
    border: 0;
  }
  .salescast-hero::before {
    position: absolute;
    z-index: -1;
    inset: 0;
    background-image:
      linear-gradient(rgba(148, 163, 184, .055) 1px, transparent 1px),
      linear-gradient(90deg, rgba(148, 163, 184, .055) 1px, transparent 1px);
    background-size: 34px 34px;
    content: "";
    mask-image: linear-gradient(90deg, transparent, #000 30%, #000 85%, transparent);
  }
  .salescast-hero::after {
    position: absolute;
    z-index: -1;
    right: -12%;
    bottom: 0;
    left: -12%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(45, 212, 191, .55), transparent);
    box-shadow: 0 0 24px rgba(45, 212, 191, .28);
    content: "";
    animation: scan-line 8s ease-in-out infinite alternate;
  }
  .salescast-eyebrow {
    margin: 0 0 .6rem;
    color: var(--sc-teal);
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .16em;
    text-transform: uppercase;
  }
  .salescast-title {
    margin: 0;
    color: var(--sc-text);
    font-size: clamp(2rem, 4vw, 3.2rem);
    font-weight: 750;
    letter-spacing: -.055em;
    line-height: 1.08;
  }
  .salescast-title span {
    color: var(--sc-teal);
    text-shadow: 0 0 24px rgba(45, 212, 191, .23);
  }
  .salescast-description {
    max-width: 690px;
    margin: .8rem 0 0;
    color: #b4c1d1;
    font-size: 1rem;
    line-height: 1.65;
  }
  .salescast-status-row {
    display: flex;
    flex-wrap: wrap;
    gap: .55rem;
    margin-top: 1.35rem;
  }
  .salescast-status {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    padding: .35rem .65rem;
    border: 1px solid rgba(148, 163, 184, .17);
    border-radius: 999px;
    color: #cbd5e1;
    background: rgba(15, 23, 42, .68);
    font-size: .77rem;
  }
  .salescast-status-dot {
    width: .42rem;
    height: .42rem;
    border-radius: 999px;
    background: var(--sc-muted);
  }
  .salescast-status-dot.is-ready {
    background: var(--sc-emerald);
    box-shadow: 0 0 10px rgba(16, 185, 129, .45);
  }

  .metric-card {
    --metric-accent: var(--sc-teal);
    position: relative;
    isolation: isolate;
    overflow: hidden;
    min-height: 132px;
    padding: 1.05rem 1.15rem;
    border: 1px solid rgba(148, 163, 184, .14);
    border-radius: 16px;
    background:
      radial-gradient(ellipse at 100% 0%, color-mix(in srgb, var(--metric-accent) 13%, transparent), transparent 58%),
      linear-gradient(145deg, rgba(23, 32, 51, .96), rgba(17, 24, 39, .97));
    box-shadow: 0 8px 24px rgba(0, 0, 0, .12);
    transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
  }
  .metric-card::before {
    position: absolute;
    z-index: -1;
    inset: auto 12% -45% 12%;
    height: 80%;
    border-radius: 50%;
    background: var(--metric-accent);
    filter: blur(48px);
    opacity: .08;
    content: "";
    transition: opacity .2s ease;
  }
  .metric-card:hover {
    transform: translateY(-3px);
    border-color: color-mix(in srgb, var(--metric-accent) 48%, var(--sc-border));
    box-shadow: 0 12px 30px rgba(0, 0, 0, .22);
  }
  .metric-card:hover::before { opacity: .16; }
  .metric-label {
    color: var(--sc-muted);
    font-size: .77rem;
    font-weight: 600;
    letter-spacing: .045em;
    text-transform: uppercase;
  }
  .metric-value {
    overflow-wrap: anywhere;
    margin-top: .55rem;
    color: var(--sc-text);
    font-size: clamp(1.35rem, 2vw, 1.85rem);
    font-weight: 730;
    letter-spacing: -.035em;
    line-height: 1.15;
  }
  .metric-detail { margin-top: .42rem; color: #718096; font-size: .75rem; }
  .accent-purple { --metric-accent: var(--sc-purple); }
  .accent-emerald { --metric-accent: var(--sc-emerald); }
  .accent-blue { --metric-accent: var(--sc-blue); }
  .accent-pink { --metric-accent: var(--sc-pink); }

  .section-heading {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 1rem;
    margin: 1.8rem 0 .85rem;
  }
  .section-heading h2 { margin: 0; font-size: 1.2rem; font-weight: 680; }
  .section-heading p { margin: .25rem 0 0; color: var(--sc-muted); font-size: .85rem; }
  .insight-card {
    height: 100%;
    padding: 1.1rem 1.2rem;
    border: 1px solid rgba(148, 163, 184, .14);
    border-radius: 15px;
    background:
      radial-gradient(circle at 100% 0%, rgba(139, 92, 246, .11), transparent 42%),
      rgba(17, 24, 39, .83);
    transition: border-color .18s ease, transform .18s ease;
  }
  .insight-card:hover { transform: translateY(-2px); border-color: rgba(139, 92, 246, .35); }
  .insight-card h3 { margin: 0 0 .35rem; font-size: .95rem; }
  .insight-card p { margin: 0; color: var(--sc-muted); font-size: .82rem; line-height: 1.55; }
  .electric-panel {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    margin: .7rem 0 1rem;
    padding: 1rem 1.15rem;
    border: 1px solid rgba(45, 212, 191, .42);
    border-radius: 16px;
    background:
      radial-gradient(ellipse at 100% 0%, rgba(45, 212, 191, .12), transparent 42%),
      linear-gradient(135deg, rgba(17, 24, 39, .96), rgba(23, 32, 51, .9));
    box-shadow: 0 0 28px rgba(45, 212, 191, .08);
  }
  .electric-panel::before {
    position: absolute;
    z-index: -1;
    inset: 0;
    border-radius: inherit;
    background: none;
    content: "";
    opacity: .32;
    pointer-events: none;
    mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
    mask-composite: exclude;
    padding: 1px;
  }
  @supports (mask-composite: exclude) {
    .electric-panel::before {
      background: conic-gradient(from 0deg, transparent 0 65%, rgba(45, 212, 191, .75) 78%, rgba(139, 92, 246, .6) 86%, transparent 100%);
      animation: electric-rotate 12s linear infinite;
    }
  }
  .electric-panel h3 { margin: 0 0 .3rem; font-size: 1rem; }
  .electric-panel p { margin: 0; color: var(--sc-muted); font-size: .84rem; line-height: 1.5; }
  .info-box, .warn-box {
    padding: 1rem 1.1rem;
    border-radius: 12px;
    color: #cbd5e1;
    line-height: 1.55;
  }
  .info-box { border: 1px solid rgba(96, 165, 250, .19); border-left: 3px solid var(--sc-blue); background: rgba(30, 58, 95, .22); }
  .warn-box { border: 1px solid rgba(244, 132, 95, .2); border-left: 3px solid #f4845f; background: rgba(80, 45, 15, .28); }
  [data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid rgba(148, 163, 184, .13);
    border-radius: 12px;
    overflow: hidden;
  }
  [data-testid="stBaseButton-primary"] {
    border: 1px solid rgba(45, 212, 191, .45);
    background: linear-gradient(100deg, #0f766e, #0e7490);
    box-shadow: 0 5px 20px rgba(45, 212, 191, .12);
    transition: filter .18s ease, transform .18s ease;
  }
  [data-testid="stBaseButton-primary"]:hover { filter: brightness(1.12); transform: translateY(-1px); }
  [data-testid="stBaseButton-secondary"] {
    border-color: rgba(148, 163, 184, .22);
    background: rgba(23, 32, 51, .72);
  }
  :focus-visible { outline: 2px solid var(--sc-teal) !important; outline-offset: 2px; }

  @keyframes scan-line {
    from { transform: translateY(-12px); opacity: .35; }
    to { transform: translateY(1px); opacity: .8; }
  }
  @keyframes logo-arrive {
    from { opacity: 0; transform: translateY(5px) scale(.92); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
  @keyframes logo-breathe {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-2px); }
  }
  @keyframes electric-rotate { to { transform: rotate(360deg); } }
  @keyframes title-reveal {
    from { opacity: 0; transform: translateY(7px); filter: blur(3px); }
    to { opacity: 1; transform: translateY(0); filter: blur(0); }
  }
  .salescast-title--reveal { animation: title-reveal .75s cubic-bezier(.2, .7, .2, 1) both; }

  @media (max-width: 760px) {
    .block-container { padding: 1.25rem 1rem 2.5rem; }
    .salescast-hero { border-radius: 16px; }
    .metric-card { min-height: 116px; padding: .9rem; }
    .metric-detail { font-size: .7rem; }
    .section-heading { align-items: start; flex-direction: column; gap: .25rem; }
  }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      scroll-behavior: auto !important;
      animation-duration: .01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: .01ms !important;
    }
  }
</style>
"""
