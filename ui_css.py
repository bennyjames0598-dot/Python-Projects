from __future__ import annotations
import streamlit as st

def inject_css(theme: dict):
    st.markdown(
        f"""
        <style>
        html, body, .stApp {{ background: {theme['DARK_BG']} !important; color: {theme['TEXT']} !important; }}
        header[data-testid="stHeader"] {{ background: {theme['DARK_BG']}; position: relative !important; z-index: 999 !important; }}
        footer {{ visibility: hidden; }}
        #MainMenu {{ visibility: hidden; }}

        .block-container {{ background: {theme['DARK_BG']}; padding-top: 2.4rem !important; padding-bottom: 1.2rem !important; }}
        section[data-testid="stSidebar"] {{ background: {theme['PANEL_BG']}; border-right: 1px solid {theme['BORDER']}; }}

        /* KPI cards */
        div[data-testid="stMetric"] {{ background: {theme['CARD_BG']}; border: 1px solid {theme['BORDER']}; border-radius: 16px; padding: 14px 16px; box-shadow: 0 10px 24px rgba(0,0,0,0.35); }}
        div[data-testid="stMetricLabel"] > div {{ color: {theme['MUTED']} !important; font-size: 0.95rem; }}
        div[data-testid="stMetricValue"] > div {{ color: {theme['TEXT']} !important; font-weight: 900; }}

        /* Chart container */
        .plotly-wrap {{ position: relative; border: 1px solid {theme['BORDER']}; border-radius: 12px; background:{theme['DARK_BG']}; }}
        .plotly-scroll {{ overflow-x: scroll !important; overflow-y: hidden; width: 100%; background: rgba(255,255,255,0.02); white-space: nowrap; position: relative; }}
        .plotly-scroll::-webkit-scrollbar {{ height: 12px; }}
        .plotly-scroll::-webkit-scrollbar-thumb {{ background: {theme['ACCENT_BLUE']}; border-radius: 6px; }}

        /* Modebar pinned top-right */
        .plotly .modebar, .modebar-container {{ position: absolute !important; top: 6px !important; right: 10px !important; z-index: 9999 !important; }}

        /* Control strip */
        .ctrl-strip {{ display:flex; align-items:center; gap:8px; margin:6px 0 8px 0; }}
        .ctrl-btn {{ background: {theme['CARD_BG']}; color:{theme['TEXT']}; border:1px solid {theme['BORDER']}; padding:4px 8px; border-radius:8px; cursor:pointer; font-size:12px; }}
        .ctrl-btn:hover {{ border-color:{theme['ACCENT_BLUE']}; }}

        /* Legend */
        .legend-row {{ display:flex; gap:12px; flex-wrap:wrap; align-items:center; justify-content:flex-end; }}
        .legend-item {{ display:flex; align-items:center; gap:6px; color:{theme['TEXT']}; font-size:12px; }}
        .legend-swatch {{ width:12px; height:12px; border-radius:2px; display:inline-block; }}

        /* Title */
        .title-h1 {{ font-size: 32px; font-weight: 900; color: {theme['TEXT']}; margin: 0 0 8px 0; }}

        /* Global text & links */
        .stApp, .stApp p, .stApp span, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{ color: {theme['TEXT']} !important; }}
        a, a:visited {{ color: {theme['ACCENT_BLUE']} !important; }}

        /* Widgets */
        div[data-baseweb="select"] > div, .stMultiSelect, .stSelectbox, .stTextInput, .stDateInput, .stNumberInput {{
          background: {theme['CARD_BG']} !important; color: {theme['TEXT']} !important; border: 1px solid {theme['BORDER']} !important; border-radius: 10px !important;
        }}
        div[data-baseweb="select"] * {{ color: {theme['TEXT']} !important; }}
        .stRadio > div {{ background: {theme['CARD_BG']}; border: 1px solid {theme['BORDER']}; border-radius: 12px; padding: 6px; }}
        .stRadio label {{ color: {theme['TEXT']} !important; }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{ border-bottom: 1px solid {theme['BORDER']} !important; }}
        .stTabs [data-baseweb="tab"] {{ color: {theme['TEXT']} !important; background: {theme['CARD_BG']} !important; border: 1px solid transparent; margin-right: 6px; border-top-left-radius: 10px; border-top-right-radius: 10px; }}
        .stTabs [aria-selected="true"] {{ border-color: {theme['BORDER']} !important; box-shadow: 0 0 0 2px rgba(8,88,255,0.2); }}

        /* Buttons */
        .stButton button, .stDownloadButton button {{ background: {theme['ACCENT_BLUE']} !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 700 !important; }}
        .stButton button:hover, .stDownloadButton button:hover {{ filter: brightness(1.1); }}
        </style>
        """,
        unsafe_allow_html=True,
    )
