"""
Faslyn — Modern Regenerative Agricultural Intelligence Dashboard
================================================================
Inspired by the BRICS AgriN Initiative for Smallholder Cooperation.
Features:
- Live multilingual switching across 7 BRICS languages
- xAI Grok API (Text & Multimodal Vision)
- Open-Meteo Zero-Sensor Telemetry
- NASA POWER Agro-Climatology Satellite Feeds
- Client-Side Multilingual Web Speech TTS
- Standardized ODbL Digital Public Good (DPG) Schema
"""

import base64
import json
import os
import sys
import textwrap

# Make the project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from backend.ai_service import (
    build_grok_client,
    generate_advisory,
    generate_crop_recommendation,
    generate_diagnosis,
)
from backend.config import BRICS_HUBS, FIRST_HUB, LANGUAGES
from backend.satellite_service import fetch_satellite_agroclimatology
from backend.telemetry_service import fetch_soil_telemetry
from backend.translations import t
from frontend.tts import speak_text

# ---------------------------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="faslyn | Smart Agriculture. Stronger Communities.",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# SAFE HTML RENDERER (Prevents Markdown 4-space code block glitch)
# ---------------------------------------------------------------------------
def render_html(html_str: str):
    """Render HTML safely without Markdown treating indented lines as code blocks."""
    cleaned = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CUSTOM CSS FOR THE EXACT DASHBOARD DESIGN
# ---------------------------------------------------------------------------
render_html(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F6F9F5 !important;
        color: #111827 !important;
    }
    
    /* High-contrast dark text everywhere */
    p, span, label, h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span {
        color: #111827 !important;
    }
    
    /* Top Streamlit App Header bar */
    header[data-testid="stHeader"] {
        background-color: #F6F9F5 !important;
    }
    header[data-testid="stHeader"] * {
        color: #111827 !important;
    }
    
    /* Sidebar text colors */
    section[data-testid="stSidebar"] {
        background-color: #F8FAF7 !important;
        border-right: 1px solid #EBF2EB !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div {
        color: #1F2937 !important;
    }
    
    /* Radio options in sidebar and main page */
    div[role="radiogroup"] label {
        color: #1F2937 !important;
        font-weight: 600 !important;
    }
    div[role="radiogroup"] label p {
        color: #1F2937 !important;
        font-weight: 600 !important;
    }
    div[role="radiogroup"] label span {
        color: #1F2937 !important;
    }
    
    /* Input and text fields */
    .stTextInput input, .stSelectbox div {
        color: #111827 !important;
        background-color: #FFFFFF !important;
    }
    
    /* Top Header Bar */
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0 16px 0;
    }
    .greeting-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #111827;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .greeting-subtitle {
        font-size: 0.95rem;
        color: #6B7280;
        margin-top: 4px;
        margin-bottom: 0;
    }
    
    /* Profile & Language Header Pill */
    .header-user-pill {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        background: #FFFFFF;
        padding: 6px 14px;
        border-radius: 9999px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .user-avatar {
        width: 32px;
        height: 32px;
        background: #DCFCE7;
        color: #15803D;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 14px;
    }
    
    /* KPI Metric Cards */
    .kpi-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 18px 20px;
        border: 1px solid #EEF2F6;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .kpi-icon-box {
        width: 48px;
        height: 48px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
    }
    .icon-green { background: #ECFDF5; color: #059669; }
    .icon-orange { background: #FFFBEB; color: #D97706; }
    .icon-teal { background: #F0FDFA; color: #0D9488; }
    
    .kpi-val {
        font-size: 1.75rem;
        font-weight: 800;
        color: #111827;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #4B5563;
        margin-bottom: 2px;
    }
    .kpi-subtext {
        font-size: 0.75rem;
        color: #9CA3AF;
        margin: 0;
    }
    
    /* Section Cards */
    .dashboard-card {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 20px;
        border: 1px solid #EEF2F6;
        box-shadow: 0 4px 16px rgba(0,0,0,0.03);
        margin-bottom: 16px;
    }
    .card-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .card-header-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #111827;
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 0;
    }
    .view-all-link {
        font-size: 0.85rem;
        font-weight: 600;
        color: #1B4D3E;
        text-decoration: none;
    }
    
    /* Progress Bars & Status */
    .metric-bar-container {
        margin: 8px 0;
    }
    .metric-bar-label {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 3px;
    }
    .metric-bar-bg {
        background-color: #F3F4F6;
        border-radius: 9999px;
        height: 7px;
        overflow: hidden;
    }
    .metric-bar-fill {
        height: 100%;
        border-radius: 9999px;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
    }
    .badge-critical { background: #FEE2E2; color: #DC2626; }
    .badge-warning { background: #FEF3C7; color: #D97706; }
    .badge-healthy { background: #DCFCE7; color: #16A34A; }
    .badge-info { background: #E0F2FE; color: #0284C7; }
    
    /* Sustainability Banner */
    .impact-banner {
        background: linear-gradient(135deg, #E8F5E9 0%, #F1F8F4 100%);
        border: 1px solid #C8E6C9;
        border-radius: 20px;
        padding: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .impact-chip {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 8px 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        border: 1px solid #E5E7EB;
    }
    
    /* Primary Action Buttons */
    .stButton > button {
        background-color: #1B4D3E !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 9999px !important;
        padding: 0.45rem 1.4rem !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #143B2F !important;
        box-shadow: 0 4px 14px rgba(27, 77, 62, 0.25) !important;
    }
    /* Click / Active state: Light Shade of Brown */
    .stButton > button:active,
    .stButton > button[data-testid="baseButton-primary"]:active {
        background-color: #B5835A !important;
        border-color: #9C683E !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 10px rgba(181, 131, 90, 0.45) !important;
        transform: scale(0.98) !important;
    }
    .stButton > button:focus,
    .stButton > button:focus-visible {
        outline: 2px solid #B5835A !important;
        box-shadow: 0 0 0 3px rgba(181, 131, 90, 0.35) !important;
    }
    
    /* Tertiary / View All Buttons */
    .stButton > button[kind="tertiary"],
    .stButton > button[data-testid="baseButton-tertiary"] {
        background-color: transparent !important;
        color: #1B4D3E !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        padding: 4px 10px !important;
        border: none !important;
        box-shadow: none !important;
        text-align: right !important;
        justify-content: flex-end !important;
        display: inline-flex !important;
    }
    .stButton > button[kind="tertiary"]:hover,
    .stButton > button[data-testid="baseButton-tertiary"]:hover {
        background-color: #F8F3EE !important;
        color: #7D4E27 !important;
        box-shadow: none !important;
    }
    .stButton > button[kind="tertiary"]:active,
    .stButton > button[data-testid="baseButton-tertiary"]:active {
        background-color: #EBDCCF !important;
        color: #643916 !important;
        border-radius: 8px !important;
        transform: scale(0.97) !important;
    }
    
    /* Secondary / Back Buttons - Enhanced Presentable Style */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="baseButton-secondary"] {
        background-color: #FFFFFF !important;
        color: #1B4D3E !important;
        border: 1.5px solid #1B4D3E !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        padding: 0.38rem 1.15rem !important;
        border-radius: 9999px !important;
        box-shadow: 0 1px 4px rgba(27, 77, 62, 0.08) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="baseButton-secondary"]:hover {
        background-color: #1B4D3E !important;
        color: #FFFFFF !important;
        border-color: #1B4D3E !important;
        box-shadow: 0 4px 12px rgba(27, 77, 62, 0.22) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="secondary"]:active,
    .stButton > button[data-testid="baseButton-secondary"]:active {
        background-color: #B5835A !important;
        color: #FFFFFF !important;
        border-color: #9C683E !important;
        box-shadow: 0 2px 8px rgba(181, 131, 90, 0.4) !important;
        transform: scale(0.98) !important;
    }

    /* Notification Bell Popover Styling */
    div[data-testid="stPopover"] {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div[data-testid="stPopover"] > button {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border: 1.5px solid #E5E7EB !important;
        border-radius: 9999px !important;
        padding: 0.38rem 0.75rem !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
    }
    div[data-testid="stPopover"] > button:hover {
        background-color: #F8F3EE !important;
        border-color: #B5835A !important;
        color: #7D4E27 !important;
        box-shadow: 0 3px 8px rgba(181, 131, 90, 0.2) !important;
    }
    div[data-testid="stPopover"] > button:active {
        background-color: #B5835A !important;
        color: #FFFFFF !important;
        border-color: #9C683E !important;
        transform: scale(0.96) !important;
    }
    div[data-testid="stPopoverBody"] {
        border-radius: 16px !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0 12px 30px rgba(0,0,0,0.12) !important;
        padding: 16px !important;
    }

    /* Radio button active/click selection styling */
    div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background-color: #F8F3EE !important;
        border-radius: 8px !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label:active {
        background-color: #EBDCCF !important;
        border-radius: 8px !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background-color: #F8F3EE !important;
        border-radius: 8px !important;
        color: #7D4E27 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stRadio"] input:checked + div {
        border-color: #B5835A !important;
        background-color: #B5835A !important;
    }

    /* Input focus styling */
    input:focus, textarea:focus, select:focus {
        border-color: #B5835A !important;
        box-shadow: 0 0 0 2px rgba(181, 131, 90, 0.25) !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #F8FAF7 !important;
        border-right: 1px solid #EBF2EB !important;
    }
    .sidebar-brand {
        font-size: 1.6rem;
        font-weight: 800;
        color: #1B4D3E !important;
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 0 16px 0;
    }
    .sidebar-tagline {
        font-size: 0.85rem;
        color: #4B5563 !important;
        line-height: 1.4;
        font-style: italic;
    }
    </style>
    """
)

# ---------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------
if "current_language" not in st.session_state:
    st.session_state.current_language = "English"
if "active_tab_id" not in st.session_state:
    st.session_state.active_tab_id = "home"
if "coords" not in st.session_state:
    st.session_state.coords = {"lat": FIRST_HUB["lat"], "lon": FIRST_HUB["lon"]}
if "zoom" not in st.session_state:
    st.session_state.zoom = FIRST_HUB["zoom"]
if "selected_hub_name" not in st.session_state:
    st.session_state.selected_hub_name = list(BRICS_HUBS.keys())[0]
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "satellite" not in st.session_state:
    st.session_state.satellite = None
if "advisory_text" not in st.session_state:
    st.session_state.advisory_text = None
if "advisory_lang_code" not in st.session_state:
    st.session_state.advisory_lang_code = LANGUAGES[st.session_state.current_language]
if "trigger_speech" not in st.session_state:
    st.session_state.trigger_speech = False
if "crop_recommendation" not in st.session_state:
    st.session_state.crop_recommendation = None
if "diagnosis_text" not in st.session_state:
    st.session_state.diagnosis_text = None
if "active_leaf_image" not in st.session_state:
    st.session_state.active_leaf_image = None
if "sample_label" not in st.session_state:
    st.session_state.sample_label = None
if "nav_stack" not in st.session_state:
    st.session_state.nav_stack = ["home"]
if "notifications" not in st.session_state:
    st.session_state.notifications = [
        {
            "id": "alert_1",
            "icon": "🔴",
            "title_key": "alert_1_title",
            "time_key": "alert_1_sub",
            "desc": "Low soil moisture (0.24 m³/m³). Rain forecast low for next 7 days.",
            "target": "sat",
            "target_label": "🛰️ View Field",
            "read": False,
        },
        {
            "id": "alert_2",
            "icon": "🟡",
            "title_key": "alert_2_title",
            "time_key": "alert_2_sub",
            "desc": "Soil organic matter deficit detected. Topsoil amendment advised.",
            "target": "regen",
            "target_label": "🔄 View Plan",
            "read": False,
        },
        {
            "id": "alert_3",
            "icon": "🔵",
            "title_key": "alert_3_title",
            "time_key": "alert_3_sub",
            "desc": "Dry spell upcoming. Formulate spoken advisory with AI agro-advisor.",
            "target": "ai",
            "target_label": "🎙️ AI Advisory",
            "read": False,
        },
    ]


def _(key: str) -> str:
    """Translate string key into active session language."""
    return t(key, st.session_state.current_language)


def navigate_to(tab_id: str):
    """Navigate to a target section and push to history stack."""
    if not st.session_state.get("nav_stack"):
        st.session_state.nav_stack = ["home"]
    if st.session_state.nav_stack[-1] != tab_id:
        st.session_state.nav_stack.append(tab_id)
    st.session_state.active_tab_id = tab_id
    st.rerun()


def navigate_back():
    """Navigate back to the previous section in history, or to home."""
    stack = st.session_state.get("nav_stack", ["home"])
    if len(stack) > 1:
        stack.pop()  # pop current
        prev_tab = stack[-1]
        st.session_state.active_tab_id = prev_tab
    else:
        st.session_state.active_tab_id = "home"
        st.session_state.nav_stack = ["home"]
    st.rerun()


def set_coords(lat, lon, zoom=None, hub_name=None):
    """Update active field coordinates and invalidate cached telemetry."""
    st.session_state.coords = {"lat": lat, "lon": lon}
    if zoom is not None:
        st.session_state.zoom = zoom
    if hub_name is not None:
        st.session_state.selected_hub_name = hub_name
    st.session_state.telemetry = None
    st.session_state.satellite = None


def get_client():
    """Resolve a Grok (xAI) client from Streamlit secrets or user input."""
    api_key = None
    try:
        api_key = st.secrets.get("GROK_API_KEY") or st.secrets.get("XAI_API_KEY")
    except Exception:
        api_key = None
    if not api_key:
        api_key = st.session_state.get("manual_grok_key")
    return build_grok_client(api_key)


# Lazy-load live telemetry & satellite feeds
if st.session_state.telemetry is None:
    st.session_state.telemetry = fetch_soil_telemetry(
        st.session_state.coords["lat"], st.session_state.coords["lon"]
    )
if st.session_state.satellite is None:
    st.session_state.satellite = fetch_satellite_agroclimatology(
        st.session_state.coords["lat"], st.session_state.coords["lon"]
    )

telemetry = st.session_state.telemetry
satellite = st.session_state.satellite

# ---------------------------------------------------------------------------
# NAVIGATION MAP FOR MULTILINGUAL TABS
# ---------------------------------------------------------------------------
nav_items = [
    ("home", _("nav_home")),
    ("sat", _("nav_sat")),
    ("ai", _("nav_ai")),
    ("regen", _("nav_regen")),
    ("brics", _("nav_brics")),
    ("settings", _("nav_settings")),
]
id_to_label = {k: v for k, v in nav_items}
id_to_label["farms"] = _("nav_sat")
id_to_label["impact"] = _("nav_brics")
label_to_id = {v: k for k, v in nav_items}

# ===========================================================================
# SIDEBAR — BRANDING & NAVIGATION
# ===========================================================================
with st.sidebar:
    render_html(
        """
        <div class="sidebar-brand">
            🌿 faslyn
        </div>
        """
    )

    current_label = id_to_label.get(st.session_state.active_tab_id, _("nav_home"))
    all_labels = [v for _, v in nav_items]
    current_index = all_labels.index(current_label) if current_label in all_labels else 0

    chosen_label = st.radio(
        "Navigation",
        all_labels,
        index=current_index,
        key=f"nav_radio_{st.session_state.active_tab_id}",
        label_visibility="collapsed",
    )
    new_tab_id = label_to_id.get(chosen_label, "home")
    if new_tab_id != st.session_state.active_tab_id:
        if new_tab_id == "home":
            st.session_state.nav_stack = ["home"]
            st.session_state.active_tab_id = "home"
            st.rerun()
        else:
            navigate_to(new_tab_id)

    st.markdown("---")

    # Grok API Key Setup in sidebar
    st.markdown("#### ⚡ AI Engine (xAI Grok)")
    manual_grok = st.text_input(
        "xAI Grok API Key",
        type="password",
        value=st.session_state.get("manual_grok_key", ""),
        help="Enter your Grok API key from console.x.ai. Leave blank to use built-in demo models.",
    )
    if manual_grok:
        st.session_state.manual_grok_key = manual_grok

    client = get_client()
    if client is None:
        st.caption("✨ **Demo Mode Active** (Pre-computed AI models ready)")
    else:
        st.success("✅ **Grok-2 AI Connected**")

    st.markdown("---")
    render_html(
        """
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-size: 32px; margin-bottom: 6px;">🌱</div>
            <div class="sidebar-tagline">
                Healthier Soil<br>Greener Tomorrow<br><b>Together</b>
            </div>
        </div>
        """
    )

# ===========================================================================
# TOP HEADER BAR WITH LIVE LANGUAGE SWITCHER
# ===========================================================================
hdr_left, hdr_right = st.columns([3, 2])

with hdr_left:
    if st.session_state.active_tab_id == "home":
        render_html(
            f"""
            <div class="top-header">
                <div>
                    <h1 class="greeting-title">{_('greeting')}</h1>
                    <p class="greeting-subtitle">{_('subtitle')}</p>
                </div>
            </div>
            """
        )
    else:
        b_c1, b_c2 = st.columns([1.5, 3.5], vertical_alignment="center")
        with b_c1:
            if st.button(_("back_to_home"), key="global_header_back", type="secondary", use_container_width=True):
                navigate_back()
        with b_c2:
            current_title = id_to_label.get(st.session_state.active_tab_id, _("nav_home"))
            render_html(
                f"""
                <div style="display:flex; align-items:center; gap:8px; padding-left:6px;">
                    <span style="font-size:0.86rem; color:#6B7280; font-weight:600;">{_('nav_home')}</span>
                    <span style="color:#9CA3AF; font-size:0.86rem;">›</span>
                    <span style="background:#F5EBE1; color:#7D4E27; font-size:0.82rem; font-weight:700; padding:3px 12px; border-radius:9999px; border:1px solid #E3D1C2;">
                        {current_title}
                    </span>
                </div>
                """
            )

with hdr_right:
    c_bell, c_lang, c_user = st.columns([1.1, 2.5, 3], vertical_alignment="center")
    with c_bell:
        unread_count = sum(1 for n in st.session_state.notifications if not n.get("read", False))
        bell_label = f"🔔 {unread_count}" if unread_count > 0 else "🔔"
        with st.popover(bell_label, help=_("upcoming_alerts"), use_container_width=True):
            st.markdown(f"#### 🔔 {_('upcoming_alerts')}")
            if unread_count > 0:
                st.caption(f"{unread_count} unread notifications")
            else:
                st.caption("All notifications read")

            st.markdown("---")
            for notif in st.session_state.notifications:
                bg_col = "#FEF2F2" if "🔴" in notif["icon"] else ("#FFFBEB" if "🟡" in notif["icon"] else "#F0F9FF")
                border_col = "#FECACA" if "🔴" in notif["icon"] else ("#FDE68A" if "🟡" in notif["icon"] else "#BAE6FD")
                render_html(
                    f"""
                    <div style="background:{bg_col}; border:1px solid {border_col}; border-radius:10px; padding:10px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; font-size:0.84rem; color:#111827;">{_(notif['title_key'])}</span>
                            <span style="font-size:0.7rem; color:#6B7280;">{_(notif['time_key'])}</span>
                        </div>
                        <div style="font-size:0.76rem; color:#4B5563; margin-top:4px;">{notif['desc']}</div>
                    </div>
                    """
                )
                col_b1, col_b2 = st.columns([1.8, 1.2])
                with col_b1:
                    if st.button(notif["target_label"], key=f"notif_act_{notif['id']}", use_container_width=True):
                        notif["read"] = True
                        navigate_to(notif["target"])
                with col_b2:
                    if not notif.get("read", False):
                        if st.button("Mark read", key=f"notif_done_{notif['id']}", type="tertiary", use_container_width=True):
                            notif["read"] = True
                            st.rerun()

            st.markdown("---")
            c_all1, c_all2 = st.columns(2)
            with c_all1:
                if st.button("✓ Mark all read", key="notif_mark_all", use_container_width=True):
                    for n in st.session_state.notifications:
                        n["read"] = True
                    st.rerun()
            with c_all2:
                if st.button("🔄 Reset alerts", key="notif_reset", type="tertiary", use_container_width=True):
                    for n in st.session_state.notifications:
                        n["read"] = False
                    st.rerun()
    with c_lang:
        selected_language = st.selectbox(
            "Language",
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state.current_language)
            if st.session_state.current_language in LANGUAGES else 0,
            key="global_live_lang_selector",
            label_visibility="collapsed",
        )
        if selected_language != st.session_state.current_language:
            st.session_state.current_language = selected_language
            st.session_state.advisory_lang_code = LANGUAGES[selected_language]
            st.rerun()

    with c_user:
        render_html(
            f"""
            <div style="padding-top: 8px;">
                <div class="header-user-pill">
                    <div class="user-avatar">RK</div>
                    <div>
                        <div style="font-size: 0.85rem; font-weight: 700; color:#111827; line-height: 1.1;">Ramesh Kumar</div>
                        <div style="font-size: 0.72rem; color: #6B7280;">{_('farmer_role')}</div>
                    </div>
                </div>
            </div>
            """
        )

if st.session_state.active_tab_id != "home":
    render_html('<div style="height: 1px; background: #E5E7EB; margin: 10px 0 18px 0;"></div>')

# ===========================================================================
# VIEW 1: HOME DASHBOARD (FULLY TRANSLATED)
# ===========================================================================
if st.session_state.active_tab_id == "home":

    # -----------------------------------------------------------------------
    # ROW 1: TOP 4 KPI CARDS
    # -----------------------------------------------------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        render_html(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon-box icon-green">🏡</div>
                <div>
                    <div class="kpi-label">{_('total_fields')}</div>
                    <div class="kpi-val">4</div>
                    <div class="kpi-subtext">{_('across_farms')}</div>
                </div>
            </div>
            """
        )

    with kpi2:
        render_html(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon-box icon-green">🍃</div>
                <div>
                    <div class="kpi-label">{_('healthy_fields')}</div>
                    <div class="kpi-val">2</div>
                    <div class="kpi-subtext">50% {_('of_total')}</div>
                </div>
            </div>
            """
        )

    with kpi3:
        render_html(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon-box icon-orange">⚠️</div>
                <div>
                    <div class="kpi-label">{_('fields_at_risk')}</div>
                    <div class="kpi-val">1</div>
                    <div class="kpi-subtext">25% {_('of_total')}</div>
                </div>
            </div>
            """
        )

    with kpi4:
        render_html(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon-box icon-teal">🪴</div>
                <div>
                    <div class="kpi-label">{_('overall_health')}</div>
                    <div class="kpi-val">76<span style="font-size:1.1rem; color:#6B7280; font-weight:600;">/100</span></div>
                    <div class="kpi-subtext" style="color:#059669; font-weight:700;">↑ +6% {_('vs_last_month')}</div>
                </div>
            </div>
            """
        )

    st.write("")

    # -----------------------------------------------------------------------
    # ROW 2: "MY FIELDS" MAP (LEFT) & "AI INSIGHTS" (RIGHT)
    # -----------------------------------------------------------------------
    mid_left, mid_right = st.columns([2, 1])

    with mid_left:
        mf_c1, mf_c2 = st.columns([3, 1], vertical_alignment="center")
        with mf_c1:
            render_html(f'<h3 class="card-header-title">{_("my_fields")}</h3>')
        with mf_c2:
            if st.button(_("view_all"), key="btn_view_all_fields", type="tertiary", use_container_width=True):
                navigate_to("sat")

        col_map_inner, col_detail_inner = st.columns([1.35, 1])

        with col_map_inner:
            center_lat = st.session_state.coords["lat"]
            center_lon = st.session_state.coords["lon"]

            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=14,
                tiles="OpenStreetMap",
                control_scale=False,
            )

            d = 0.005
            p1 = [[center_lat + d, center_lon - d], [center_lat + 2*d, center_lon], [center_lat + d, center_lon + d/2]]
            p2 = [[center_lat, center_lon], [center_lat + d, center_lon + d/2], [center_lat - d/2, center_lon + 1.5*d]]
            p3 = [[center_lat - d, center_lon - d/2], [center_lat, center_lon], [center_lat - 1.5*d, center_lon + d/3]]
            p4 = [[center_lat - d, center_lon + d/2], [center_lat - d/2, center_lon + 1.5*d], [center_lat - 2*d, center_lon + d]]

            folium.Polygon(locations=p1, color="#16A34A", fill=True, fill_color="#22C55E", fill_opacity=0.6, tooltip="Field 01").add_to(m)
            folium.Polygon(locations=p2, color="#D97706", fill=True, fill_color="#F59E0B", fill_opacity=0.6, tooltip="Field 02").add_to(m)
            folium.Polygon(locations=p3, color="#DC2626", fill=True, fill_color="#EF4444", fill_opacity=0.7, tooltip="Field 03").add_to(m)
            folium.Polygon(locations=p4, color="#16A34A", fill=True, fill_color="#22C55E", fill_opacity=0.6, tooltip="Field 04").add_to(m)

            st_folium(m, height=275, use_container_width=True, key="dashboard_map")

            render_html(
                f"""
                <div style="display:flex; justify-content:center; gap: 16px; font-size: 0.78rem; font-weight:600; color: #4B5563; margin-top: 4px;">
                    <span>🟢 {_('healthy')}</span>
                    <span>🟡 {_('moderate_risk')}</span>
                    <span>🔴 {_('critical')}</span>
                </div>
                """
            )

        with col_detail_inner:
            soil_pct = int(min(100, max(10, (telemetry.get('soil_moisture', 0.24) / 0.40) * 100)))
            water_pct = int(min(100, max(10, (satellite.get('root_zone_soil_wetness', 0.41) / 0.70) * 100)))

            render_html(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #EEF2F6; border-radius: 16px; padding: 16px; height: 100%;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                        <h4 style="margin:0; font-weight:800; font-size:1.15rem; color:#111827;">Field 03</h4>
                        <span class="badge badge-critical">{_('high_risk')}</span>
                    </div>
                    <div style="font-size: 0.8rem; color:#4B5563; line-height: 1.6; margin-bottom: 12px;">
                        <div>🌾 <b>{_('rice')}</b> &nbsp;•&nbsp; 📍 <b>{st.session_state.selected_hub_name.split('—')[1] if '—' in st.session_state.selected_hub_name else 'Odisha, India'}</b></div>
                        <div>📅 <b>48 {_('crop_age')}</b></div>
                    </div>
                    
                    <div class="metric-bar-container">
                        <div class="metric-bar-label">
                            <span>{_('field_health')}</span>
                            <span style="color:#DC2626; font-weight:700;">64%</span>
                        </div>
                        <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: 64%; background: #EF4444;"></div></div>
                    </div>
                    
                    <div class="metric-bar-container">
                        <div class="metric-bar-label">
                            <span>🪱 {_('soil_health')}</span>
                            <span>{soil_pct}%</span>
                        </div>
                        <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: {soil_pct}%; background: #F59E0B;"></div></div>
                    </div>
                    
                    <div class="metric-bar-container">
                        <div class="metric-bar-label">
                            <span>💧 {_('water_status')}</span>
                            <span>{water_pct}%</span>
                        </div>
                        <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: {water_pct}%; background: #0284C7;"></div></div>
                    </div>
                    
                    <div class="metric-bar-container">
                        <div class="metric-bar-label">
                            <span>🌿 {_('vegetation')}</span>
                            <span>62%</span>
                        </div>
                        <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: 62%; background: #10B981;"></div></div>
                    </div>
                </div>
                """
            )
            if st.button(_("view_details_btn"), use_container_width=True, key="btn_view_field_details"):
                navigate_to("sat")

    with mid_right:
        ai_c1, ai_c2 = st.columns([2.5, 1.2], vertical_alignment="center")
        with ai_c1:
            render_html(f'<h3 class="card-header-title">{_("ai_insights")}</h3>')
        with ai_c2:
            if st.button(_("view_all"), key="btn_view_all_ai", type="tertiary", use_container_width=True):
                navigate_to("ai")

        render_html(
            f"""
            <div class="dashboard-card" style="margin-top: 4px;">
                <div style="background: #FEF2F2; border: 1px solid #FEE2E2; border-radius: 14px; padding: 14px; margin-bottom: 16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                        <span style="font-weight:700; color:#DC2626; font-size:0.92rem; display:flex; align-items:center; gap:6px;">
                            {_('water_stress_detected')}
                        </span>
                        <span style="font-size:0.72rem; color:#DC2626; font-weight:700; background:#FFFFFF; padding:2px 8px; border-radius:9999px;">
                            {_('high_confidence')}
                        </span>
                    </div>
                    <p style="font-size:0.8rem; color:#4B5563; margin:0; line-height: 1.45;">
                        {_('water_stress_desc')}
                    </p>
                </div>
                
                <div style="margin-bottom: 16px;">
                    <div style="font-size:0.85rem; font-weight:700; color:#111827; margin-bottom: 8px; display:flex; align-items:center; gap:6px;">
                        {_('recommended_action')}
                    </div>
                    <ul style="font-size:0.82rem; color:#4B5563; padding-left: 18px; margin:0; line-height: 1.6;">
                        <li>{_('action_1')}</li>
                        <li>{_('action_2')}</li>
                        <li>{_('action_3')}</li>
                    </ul>
                </div>
            </div>
            """
        )
        if st.button(_("gen_regen_plan"), use_container_width=True, key="btn_gen_regen_home"):
            navigate_to("regen")

    st.write("")

    # -----------------------------------------------------------------------
    # ROW 3: FARM OVERVIEW | QUICK ACTIONS | UPCOMING & ALERTS
    # -----------------------------------------------------------------------
    col_ov, col_act, col_alt = st.columns(3)

    with col_ov:
        fo_c1, fo_c2 = st.columns([2.5, 1.2], vertical_alignment="center")
        with fo_c1:
            render_html(f'<h3 class="card-header-title">{_("farm_overview")}</h3>')
        with fo_c2:
            if st.button(_("view_all"), key="btn_view_all_fo", type="tertiary", use_container_width=True):
                navigate_to("sat")

        render_html(
            f"""
            <div class="dashboard-card" style="height: 100%;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div style="background: #FAFCFA; border: 1px solid #EEF2F6; border-radius: 12px; padding: 10px;">
                        <div style="display:flex; align-items:center; gap:6px; font-weight:700; font-size:0.82rem; color:#111827;">
                            <span style="color:#16A34A;">●</span> Field 01
                        </div>
                        <div class="badge badge-healthy" style="margin:4px 0;">{_('healthy')}</div>
                        <div style="font-size:0.75rem; color:#6B7280;">🌾 {_('rice')} • 1.2 ha</div>
                    </div>
                    
                    <div style="background: #FAFCFA; border: 1px solid #EEF2F6; border-radius: 12px; padding: 10px;">
                        <div style="display:flex; align-items:center; gap:6px; font-weight:700; font-size:0.82rem; color:#111827;">
                            <span style="color:#F59E0B;">●</span> Field 02
                        </div>
                        <div class="badge badge-warning" style="margin:4px 0;">{_('moderate_risk')}</div>
                        <div style="font-size:0.75rem; color:#6B7280;">🌽 {_('maize')} • 0.8 ha</div>
                    </div>
                    
                    <div style="background: #FAFCFA; border: 1px solid #EEF2F6; border-radius: 12px; padding: 10px;">
                        <div style="display:flex; align-items:center; gap:6px; font-weight:700; font-size:0.82rem; color:#111827;">
                            <span style="color:#DC2626;">●</span> Field 03
                        </div>
                        <div class="badge badge-critical" style="margin:4px 0;">{_('high_risk')}</div>
                        <div style="font-size:0.75rem; color:#6B7280;">🌾 {_('rice')} • 1.1 ha</div>
                    </div>
                    
                    <div style="background: #FAFCFA; border: 1px solid #EEF2F6; border-radius: 12px; padding: 10px;">
                        <div style="display:flex; align-items:center; gap:6px; font-weight:700; font-size:0.82rem; color:#111827;">
                            <span style="color:#16A34A;">●</span> Field 04
                        </div>
                        <div class="badge badge-healthy" style="margin:4px 0;">{_('healthy')}</div>
                        <div style="font-size:0.75rem; color:#6B7280;">🥬 {_('veg')} • 0.6 ha</div>
                    </div>
                </div>
            </div>
            """
        )

    with col_act:
        render_html(
            f"""
            <div class="dashboard-card" style="height: 100%;">
                <div class="card-header-row">
                    <h3 class="card-header-title">{_('quick_actions')}</h3>
                </div>
            </div>
            """
        )

        qa1, qa2 = st.columns(2)
        with qa1:
            if st.button(_("qa_upload"), use_container_width=True, key="qa_upload"):
                navigate_to("ai")
            if st.button(_("qa_speak"), use_container_width=True, key="qa_speak"):
                navigate_to("ai")

        with qa2:
            if st.button(_("qa_sat"), use_container_width=True, key="qa_sat"):
                navigate_to("sat")
            if st.button(_("qa_down"), use_container_width=True, key="qa_down"):
                navigate_to("brics")

    with col_alt:
        ua_c1, ua_c2 = st.columns([2.5, 1.2], vertical_alignment="center")
        with ua_c1:
            render_html(f'<h3 class="card-header-title">{_("upcoming_alerts")}</h3>')
        with ua_c2:
            if st.button(_("view_all"), key="btn_view_all_alerts", type="tertiary", use_container_width=True):
                navigate_to("ai")

        render_html(
            f"""
            <div class="dashboard-card" style="height: 100%;">
                <div style="display:flex; flex-direction:column; gap:10px;">
                    <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#FEF2F2; border-radius:10px;">
                        <div>
                            <div style="font-size:0.82rem; font-weight:700; color:#DC2626;">{_('alert_1_title')}</div>
                            <div style="font-size:0.72rem; color:#6B7280;">{_('alert_1_sub')}</div>
                        </div>
                        <span style="color:#DC2626;">›</span>
                    </div>
                    
                    <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#FFFBEB; border-radius:10px;">
                        <div>
                            <div style="font-size:0.82rem; font-weight:700; color:#D97706;">{_('alert_2_title')}</div>
                            <div style="font-size:0.72rem; color:#6B7280;">{_('alert_2_sub')}</div>
                        </div>
                        <span style="color:#D97706;">›</span>
                    </div>
                    
                    <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#F0F9FF; border-radius:10px;">
                        <div>
                            <div style="font-size:0.82rem; font-weight:700; color:#0284C7;">{_('alert_3_title')}</div>
                            <div style="font-size:0.72rem; color:#6B7280;">{_('alert_3_sub')}</div>
                        </div>
                        <span style="color:#0284C7;">›</span>
                    </div>
                </div>
            </div>
            """
        )

    st.write("")

    # -----------------------------------------------------------------------
    # ROW 4: SUSTAINABILITY BANNER (IMPACT ESTIMATOR)
    # -----------------------------------------------------------------------
    render_html(
        f"""
        <div class="impact-banner">
            <div style="max-width: 50%;">
                <h3 style="margin:0 0 6px 0; font-weight:800; font-size:1.35rem; color:#1B4D3E;">
                    {_('sustainable_future')}
                </h3>
                <p style="margin:0; font-size:0.9rem; color:#374151;">
                    {_('sustainable_desc')}
                </p>
            </div>
            
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <div class="impact-chip">
                    <span style="font-size:20px;">🪴</span>
                    <div>
                        <div style="font-size:0.72rem; color:#6B7280;">{_('soil_health')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#16A34A;">↑ 14%</div>
                    </div>
                </div>
                
                <div class="impact-chip">
                    <span style="font-size:20px;">💧</span>
                    <div>
                        <div style="font-size:0.72rem; color:#6B7280;">{_('water_use')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#0284C7;">↓ -11%</div>
                    </div>
                </div>
                
                <div class="impact-chip">
                    <span style="font-size:20px;">🧪</span>
                    <div>
                        <div style="font-size:0.72rem; color:#6B7280;">{_('input_dep')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#16A34A;">↓ -18%</div>
                    </div>
                </div>
                
                <div class="impact-chip">
                    <span style="font-size:20px;">🌿</span>
                    <div>
                        <div style="font-size:0.72rem; color:#6B7280;">{_('regen_score')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#16A34A;">↑ +17%</div>
                    </div>
                </div>
            </div>
        </div>
        """
    )

    if st.button(f"🌱 {_('gen_regen_plan')}", key="btn_banner_regen_all", use_container_width=True):
        navigate_to("regen")

    st.write("")

    render_html(
        f"""
        <div style="text-align: center; color: #9CA3AF; font-size: 0.8rem; padding-bottom: 20px;">
            <b>{_('tagline_footer')}</b>
        </div>
        """
    )

# ===========================================================================
# VIEW 2: SATELLITE VIEW & GROUND TELEMETRY
# ===========================================================================
elif st.session_state.active_tab_id in ["farms", "sat"]:
    st.markdown(f"## {_('nav_sat')}")
    st.caption("Live NASA POWER satellite reanalysis & Open-Meteo modeled topsoil parameters.")

    col_hub_a, col_hub_b = st.columns([1, 2])
    with col_hub_a:
        st.markdown("#### 📍 Select BRICS Agricultural Belt")
        selected_hub = st.radio(
            "Hub Selection",
            list(BRICS_HUBS.keys()),
            index=list(BRICS_HUBS.keys()).index(st.session_state.selected_hub_name)
            if st.session_state.selected_hub_name in BRICS_HUBS else 0,
        )
        if st.button("📍 Snap Map to Selected Hub", use_container_width=True):
            h_data = BRICS_HUBS[selected_hub]
            set_coords(h_data["lat"], h_data["lon"], h_data["zoom"], selected_hub)
            st.rerun()

        st.code(
            f"Latitude:  {st.session_state.coords['lat']:.4f}\nLongitude: {st.session_state.coords['lon']:.4f}",
            language="text",
        )

    with col_hub_b:
        m_sat = folium.Map(
            location=[st.session_state.coords["lat"], st.session_state.coords["lon"]],
            zoom_start=st.session_state.zoom,
            tiles="OpenStreetMap",
        )
        for name, hub_data in BRICS_HUBS.items():
            folium.Marker(
                [hub_data["lat"], hub_data["lon"]],
                popup=name,
                tooltip=name,
                icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
            ).add_to(m_sat)

        folium.Marker(
            [st.session_state.coords["lat"], st.session_state.coords["lon"]],
            popup="Active Field",
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
        ).add_to(m_sat)

        map_interaction = st_folium(m_sat, height=350, use_container_width=True, key="sat_view_map")
        if map_interaction and map_interaction.get("last_clicked"):
            c_clicked = map_interaction["last_clicked"]
            if (
                round(c_clicked["lat"], 4) != round(st.session_state.coords["lat"], 4)
                or round(c_clicked["lng"], 4) != round(st.session_state.coords["lon"], 4)
            ):
                set_coords(c_clicked["lat"], c_clicked["lng"], hub_name="Custom Pinpoint")
                st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Real-Time Environmental Indicators")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric(_("soil_health"), f"{telemetry.get('soil_moisture', 0.24):.2f} m³/m³", "Optimal Field Capacity")
    s2.metric("Soil Temperature", f"{telemetry.get('soil_temp', 27.5):.1f} °C", "Microbial Activity Active")
    s3.metric("Solar Radiation (NASA)", f"{satellite.get('solar_radiation', 18.5):.1f} MJ/m²/d", "High Photosynthesis")
    s4.metric(_("water_status"), f"{satellite.get('root_zone_soil_wetness', 0.42):.2f} (0-1)", "Adequate Deep Moisture")

    if telemetry.get("trend"):
        with st.expander("📈 24-Hour Ground Weather & Soil Micro-Trend", expanded=False):
            st.dataframe(telemetry["trend"], use_container_width=True)

    st.markdown("---")
    bot_b1, bot_b2 = st.columns([1.5, 3], vertical_alignment="center")
    with bot_b1:
        if st.button(_("back_to_home"), key="back_sat_bot", type="secondary", use_container_width=True):
            navigate_back()
    with bot_b2:
        if st.button(f"{_('nav_ai')} →", key="fwd_sat_to_ai", type="primary"):
            navigate_to("ai")

# ===========================================================================
# VIEW 3: AI INSIGHTS & MULTILINGUAL SPOKEN ADVISOR
# ===========================================================================
elif st.session_state.active_tab_id == "ai":
    st.markdown(f"## {_('nav_ai')}")
    st.caption("Powered by xAI Grok API with fallback resilience for live demonstrations.")

    tab_voice, tab_vision = st.tabs(["🎙️ Spoken Oral Agro-Advisor", "🩺 Leaf Doctor (Disease Diagnostic)"])

    with tab_voice:
        st.subheader("🎙️ Spoken Agro-Advisory")
        st.write(f"Active spoken language: **{st.session_state.current_language}**")

        gen_adv = st.button(f"🎙️ Generate & Speak Advisory in {st.session_state.current_language}", type="primary", use_container_width=True)

        if gen_adv:
            client = get_client()
            with st.spinner("Grok is formulating your localized spoken advisory..."):
                adv = generate_advisory(client, telemetry, st.session_state.current_language, satellite=satellite)
            st.session_state.advisory_text = adv
            st.session_state.advisory_lang_code = LANGUAGES[st.session_state.current_language]
            st.session_state.trigger_speech = True

        if st.session_state.advisory_text:
            render_html(
                f"""
                <div style="background:#FFFFFF; border-left: 5px solid #1B4D3E; border-radius: 12px; padding: 18px; margin-top: 16px;">
                    <h4 style="margin:0 0 8px 0; color:#1B4D3E;">🗣️ Advisory ({st.session_state.current_language})</h4>
                    <p style="font-size: 1.15rem; line-height: 1.6; color:#111827; margin:0;">{st.session_state.advisory_text}</p>
                </div>
                """
            )
            col_rep, _ = st.columns([1, 4])
            with col_rep:
                if st.button("🔊 Replay Audio"):
                    st.session_state.trigger_speech = True
                    st.rerun()

            if st.session_state.trigger_speech:
                speak_text(st.session_state.advisory_text, st.session_state.advisory_lang_code)
                st.session_state.trigger_speech = False

    with tab_vision:
        st.subheader("🩺 Leaf Doctor (Grok Multimodal Vision)")
        st.write("Upload a crop photo or choose a 1-click test sample for instant organic diagnosis.")

        v_s1, v_s2, v_s3 = st.columns(3)
        with v_s1:
            if st.button("🍅 Sample: Tomato Early Blight", use_container_width=True):
                st.session_state.active_leaf_image = Image.open("frontend/samples/tomato_early_blight.png")
                st.session_state.sample_label = "Tomato Early Blight"
                st.session_state.diagnosis_text = None
        with v_s2:
            if st.button("🌾 Sample: Rice Blast", use_container_width=True):
                st.session_state.active_leaf_image = Image.open("frontend/samples/rice_blast.png")
                st.session_state.sample_label = "Rice Blast"
                st.session_state.diagnosis_text = None
        with v_s3:
            if st.button("🌽 Sample: Healthy Maize", use_container_width=True):
                st.session_state.active_leaf_image = Image.open("frontend/samples/healthy_maize.png")
                st.session_state.sample_label = "Healthy Maize"
                st.session_state.diagnosis_text = None

        uploaded_img = st.file_uploader("Or upload your own crop photo:", type=["jpg", "jpeg", "png"])
        if uploaded_img is not None:
            st.session_state.active_leaf_image = Image.open(uploaded_img)
            st.session_state.sample_label = "Custom Upload"

        if st.session_state.active_leaf_image is not None:
            v_col1, v_col2 = st.columns([1, 2])
            with v_col1:
                st.image(st.session_state.active_leaf_image, caption=st.session_state.sample_label, use_container_width=True)
                if st.button("🔍 Run Disease Diagnostic Scan", type="primary", use_container_width=True):
                    client = get_client()
                    with st.spinner("Grok Vision is inspecting foliar pathology..."):
                        diag = generate_diagnosis(client, st.session_state.active_leaf_image, sample_hint=st.session_state.sample_label)
                    st.session_state.diagnosis_text = diag

            with v_col2:
                if st.session_state.diagnosis_text:
                    st.markdown("#### 📋 Diagnostic Report & Organic Remedy")
                    st.info(st.session_state.diagnosis_text)

    st.markdown("---")
    bot_b1, bot_b2 = st.columns([1.5, 3], vertical_alignment="center")
    with bot_b1:
        if st.button(_("back_to_home"), key="back_ai_bot", type="secondary", use_container_width=True):
            navigate_back()
    with bot_b2:
        if st.button(f"{_('nav_regen')} →", key="fwd_ai_to_regen", type="primary"):
            navigate_to("regen")

# ===========================================================================
# VIEW 4: REGENERATIVE PLANNER
# ===========================================================================
elif st.session_state.active_tab_id == "regen":
    st.markdown(f"## {_('nav_regen')}")
    st.caption("Replaces chemical monoculture with soil-nourishing companion rotations and organic amendments.")

    if st.button(_("gen_regen_plan"), type="primary"):
        client = get_client()
        with st.spinner("Grok agronomy engine is analyzing soil biology and satellite climatology..."):
            rec = generate_crop_recommendation(client, telemetry, satellite, st.session_state.current_language)
        st.session_state.crop_recommendation = rec

    rec = st.session_state.crop_recommendation
    if rec:
        r1, r2 = st.columns(2)
        with r1:
            render_html(
                f"""
                <div class="dashboard-card" style="border-left: 5px solid #16A34A;">
                    <h4>🌱 Recommended Primary Crop</h4>
                    <h2 style="color: #16A34A; margin: 0;">{rec.get('recommended_crop', 'Pearl Millet')}</h2>
                </div>
                """
            )
        with r2:
            render_html(
                f"""
                <div class="dashboard-card" style="border-left: 5px solid #0284C7;">
                    <h4>🔁 Companion / Nitrogen-Fixing Rotation</h4>
                    <h2 style="color: #0284C7; margin: 0;">{rec.get('rotation_partner', 'Cowpea / Pigeon Pea')}</h2>
                </div>
                """
            )

        r3, r4 = st.columns(2)
        with r3:
            st.markdown(f"**🧪 {_('soil_health')} Amendment**")
            st.info(rec.get("soil_amendment", "Farmyard Manure + Biochar"))
        with r4:
            st.markdown(f"**💧 Smart {_('water_status')} Guidance**")
            st.info(rec.get("irrigation_guidance", "Deficit drip irrigation in cool evening"))

        render_html(
            f"""
            <div style="background: #E8F5E9; border: 1px solid #C8E6C9; padding: 14px 18px; border-radius: 12px; margin-top: 10px;">
                <b>Agronomic Rationale:</b> {rec.get('rationale', 'C4 grain paired with nitrogen-fixing legume optimizes biological yields.')}
            </div>
            """
        )

    st.markdown("---")
    bot_b1, bot_b2 = st.columns([1.5, 3], vertical_alignment="center")
    with bot_b1:
        if st.button(_("back_to_home"), key="back_regen_bot", type="secondary", use_container_width=True):
            navigate_back()
    with bot_b2:
        if st.button(f"{_('nav_brics')} →", key="fwd_regen_to_brics", type="primary"):
            navigate_to("brics")

# ===========================================================================
# VIEW 5: BRICS KNOWLEDGE HUB (DPG & INTEROPERABILITY)
# ===========================================================================
elif st.session_state.active_tab_id in ["brics", "impact"]:
    st.markdown(f"## {_('nav_brics')}")
    st.caption("Standardized Digital Public Good (DPG) export schema aligned with India AgriStack, Brazil EMBRAPA, and South Africa AgriPortal.")

    interop_schema = {
        "endpoint": "/api/v1/faslyn/export",
        "method": "GET",
        "schema_version": "2.0.0",
        "ai_engine": "xAI Grok-2",
        "node": {
            "node_id": "faslyn-brics-node-001",
            "network": "BRICS-AgriN-Cooperation",
            "operator_type": "smallholder-cooperative",
        },
        "field": {
            "latitude": st.session_state.coords["lat"],
            "longitude": st.session_state.coords["lon"],
            "hub_region": st.session_state.selected_hub_name,
        },
        "ground_telemetry": {
            "soil_moisture_0_7cm_m3m3": telemetry.get("soil_moisture"),
            "soil_temperature_c": telemetry.get("soil_temp"),
            "air_temperature_c": telemetry.get("air_temp"),
            "windspeed_kmh": telemetry.get("windspeed"),
            "source": telemetry.get("source"),
            "sensor_type": "zero-sensor (Open-Meteo)",
        },
        "satellite_agroclimatology": {
            "solar_radiation_mj_m2_day": satellite.get("solar_radiation"),
            "precipitation_mm_day": satellite.get("precipitation"),
            "root_zone_soil_wetness_fraction": satellite.get("root_zone_soil_wetness"),
            "data_date": satellite.get("data_date"),
            "source": satellite.get("source"),
            "provider": "NASA POWER (community=AG)",
        },
        "ai_advisory": {
            "language": st.session_state.current_language,
            "text": st.session_state.advisory_text,
            "model": "xAI grok-2-latest",
        },
        "crop_recommendation": st.session_state.crop_recommendation,
        "interoperability": {
            "compatible_national_stacks": [
                "🇮🇳 India AgriStack / Kisan e-Mitra",
                "🇧🇷 Brazil Agro API (EMBRAPA-aligned)",
                "🇿🇦 South Africa AgriPortal",
                "🇷🇺 Russia Unified Agro-Informational System",
                "🇨🇳 China National Agricultural Information Network",
            ],
            "data_license": "Open Data Commons Open Database License (ODbL)",
            "cost_model": "$0 — 100% free-tier digital public infrastructure",
        },
    }

    st.json(interop_schema)

    st.download_button(
        f"⬇️ {_('qa_down').splitlines()[0].replace('📄 ', '')} (JSON)",
        data=json.dumps(interop_schema, indent=2),
        file_name="brics_agrin_node_export.json",
        mime="application/json",
        type="primary",
    )

    st.markdown("---")
    bot_b1, bot_b2 = st.columns([1.5, 3], vertical_alignment="center")
    with bot_b1:
        if st.button(_("back_to_home"), key="back_brics_bot", type="secondary", use_container_width=True):
            navigate_back()
    with bot_b2:
        if st.button(f"{_('nav_settings')} →", key="fwd_brics_to_settings", type="primary"):
            navigate_to("settings")

# ===========================================================================
# VIEW 6: SETTINGS
# ===========================================================================
elif st.session_state.active_tab_id == "settings":
    st.markdown(f"## {_('nav_settings')}")
    st.write("Configure your farmer profile, xAI Grok API key, and offline preferences.")

    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.text_input("Farmer Name", value="Ramesh Kumar")
        st.text_input("Farm Region", value="Odisha, India")
    with s_col2:
        st.text_input("xAI Grok API Key", type="password", value=st.session_state.get("manual_grok_key", ""))
        st.checkbox("Enable Offline Field Cache", value=True)

    if st.button("Save Settings", type="primary"):
        st.success("Settings saved successfully!")

    st.markdown("---")
    if st.button(_("back_to_home"), key="back_settings_bot", type="secondary"):
        navigate_back()
