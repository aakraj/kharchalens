from __future__ import annotations

import streamlit as st

ACCENT = "#2563EB"
ACCENT_SOFT = "rgba(37, 99, 235, 0.12)"
TEAL = "#0D9488"
YELLOW = "#EAB308"
YELLOW_SOFT = "#FEF9C3"
CARD_BG = "rgba(255, 255, 255, 0.92)"
MONEY_FONT = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
    '"Helvetica Neue", Arial, sans-serif'
)


def apply_theme() -> None:
    st.markdown(
        f"""
        <style>

        html, body, [class*="st-"], .block-container {{
            font-family: {MONEY_FONT};
        }}

        [data-testid^="stIcon"] {{
            font-family: "Material Symbols Rounded", sans-serif;
        }}

        .block-container{{
            padding-top: 3.2rem;
            padding-bottom: 3rem;
        }}

        .hero {{
            background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 60%, #3B82F6 100%);
            border-radius: 18px;
            padding: 1.6rem 1.9rem 1.5rem;
            margin-bottom: 1.4rem;
            color: #ffffff;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.25);
        }}
        .hero h1 {{
            margin: 0;
            font-size: 1.9rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }}
        .hero p {{
            margin: 0.35rem 0 0;
            font-size: 0.95rem;
            opacity: 0.92;
        }}

        div[data-testid="stMetric"] {{
            background: {CARD_BG};
            border: 1px solid rgba(31, 41, 55, 0.08);
            border-radius: 14px;
            padding: 0.95rem 1.1rem;
            box-shadow: 0 1px 3px rgba(31, 41, 55, 0.06);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        div[data-testid="stMetric"]:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(31, 41, 55, 0.10);
        }}
        div[data-testid="stMetric"] label {{
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            color: #6b7280;
        }}
        div[data-testid="stMetricValue"] {{
            font-family: {MONEY_FONT};
            font-size: 1.35rem;
            font-weight: 600;
            color: #111827;
            font-variant-numeric: tabular-nums;
        }}

        div[data-testid="stMetricDelta"] {{
            font-weight: 600;
        }}

        div[data-testid="stTabs"] button[data-baseweb="tab"] {{
            font-weight: 600;
            border-radius: 10px 10px 0 0;
        }}
        div[data-testid="stTabs"] button[aria-selected="true"] {{
            color: {ACCENT};
            border-bottom: 2px solid {ACCENT};
        }}

        div[data-testid="stRadio"] div[role="radiogroup"] {{
            gap: 0.4rem;
            background: rgba(31, 41, 55, 0.05);
            border-radius: 12px;
            padding: 0.25rem;
        }}
        div[data-testid="stRadio"] label {{
            border-radius: 9px;
            padding: 0.3rem 0.9rem;
            transition: background 0.15s ease, color 0.15s ease;
        }}
        div[data-testid="stRadio"] label:has(input:checked) {{
            background: #ffffff;
            color: {ACCENT};
            font-weight: 700;
            box-shadow: 0 1px 4px rgba(31, 41, 55, 0.15);
        }}
        div[data-testid="stRadio"] label:has(input:checked) > div:first-child {{
            border-color: {ACCENT};
        }}

        div[data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(31, 41, 55, 0.08);
        }}

        h2 {{
            margin-top: 1.6rem;
            letter-spacing: -0.01em;
        }}

        div[data-testid="stSuccess"] {{
            border-radius: 12px;
            border-left: 4px solid {ACCENT};
        }}

        div[data-testid="stInfo"] {{
            border-radius: 12px;
        }}

        .stat-card {{
            background: {CARD_BG};
            border: 1px solid rgba(31, 41, 55, 0.08);
            border-left: 4px solid {ACCENT};
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
            box-shadow: 0 1px 3px rgba(31, 41, 55, 0.06);
        }}
        .stat-card .stat-label {{
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: #6b7280;
        }}
        .stat-card .stat-value {{
            font-family: {MONEY_FONT};
            font-size: 1.05rem;
            font-weight: 650;
            color: #111827;
            margin-top: 0.15rem;
            word-break: break-word;
        }}

        .hl-card {{
            background: linear-gradient(160deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid rgba(31, 41, 55, 0.08);
            border-radius: 16px;
            padding: 1.05rem 1.15rem 1.15rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(31, 41, 55, 0.05);
            display: flex;
            flex-direction: column;
            min-height: 132px;
            height: 100%;
            transition: transform 0.16s ease, box-shadow 0.16s ease;
        }}
        .hl-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 28px rgba(31, 41, 55, 0.14);
        }}
        .hl-card::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: var(--hl-accent);
        }}
        .hl-top {{
            display: flex;
            align-items: center;
            gap: 0.55rem;
        }}
        .hl-ico {{
            width: 38px; height: 38px;
            border-radius: 11px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            background: var(--hl-accent-soft);
            flex: none;
        }}
        .hl-label {{
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6b7280;
            line-height: 1.2;
        }}
        .hl-value {{
            font-family: {MONEY_FONT};
            font-size: 1.28rem;
            font-weight: 750;
            color: #111827;
            margin-top: 0.55rem;
            word-break: break-word;
        }}
        .hl-bar {{
            margin-top: auto;
            height: 6px;
            border-radius: 99px;
            background: rgba(31, 41, 55, 0.08);
            overflow: hidden;
        }}
        .hl-bar > div {{
            height: 100%;
            border-radius: 99px;
            background: var(--hl-accent);
        }}

        .app-footer {{
            margin-top: 4rem;
            padding: 2.2rem 1rem 1.4rem;
            border-top: 1px solid rgba(31, 41, 55, 0.10);
            text-align: center;
        }}
        .app-footer .footer-links {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.4rem 1.6rem;
            margin-bottom: 1.1rem;
        }}
        .app-footer a {{
            color: {ACCENT};
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        .app-footer a:hover {{
            text-decoration: underline;
        }}
        .app-footer .footer-note {{
            font-size: 0.8rem;
            color: #6b7280;
            line-height: 1.5;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
        <div class="app-footer">
            <div class="footer-links">
                <a href="https://github.com/aakraj/kharchalens" target="_blank">GitHub</a>
                <a href="https://github.com/aakraj/kharchalens#readme" target="_blank">Documentation</a>
                <a href="https://github.com/aakraj/kharchalens/issues/new" target="_blank">Report an issue</a>
            </div>
            <div class="footer-note">
                KharchaLens · 100% offline — your bank statements never leave this device.<br>
                Built with Streamlit. Not affiliated with or endorsed by HDFC or SBI Bank.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
