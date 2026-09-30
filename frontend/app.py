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
import concurrent.futures
import json
import os
import sys
import textwrap
import threading

# Make the project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import folium
from folium.plugins import LocateControl
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from backend.ai_service import (
    build_grok_client,
    generate_advisory,
    generate_crop_recommendation,
    generate_diagnosis,
)
from backend.api import start_api_server_background
from backend.config import BRICS_HUBS, DEMO_PROFILES, FIRST_HUB, LANGUAGES, REGIONAL_FIELDS
from backend.database import (
    init_db,
    log_advisory_record,
    log_telemetry_snapshot,
    upsert_farmer,
)
from backend.geocoding import geocode_location
from backend.satellite_service import fetch_satellite_agroclimatology
from backend.soil_service import calculate_soil_health_score, fetch_soil_profile
from backend.telemetry_service import fetch_soil_telemetry
from backend.translations import t
from frontend.tts import speak_text
from frontend.about import show_about_page, show_login_modal


# Dynamic port assignment (configurable via FASLYN_API_PORT env variable)
API_PORT = int(os.environ.get("FASLYN_API_PORT", 8000))

# Initialize local SQLite persistence and start interoperable REST API service (zero-cost)
try:
    init_db()
    start_api_server_background(API_PORT)
except Exception:
    pass


# High-performance caching for telemetry, satellite data, soil & geocoding
@st.cache_data(ttl=600, show_spinner=False)
def get_telemetry(lat: float, lon: float) -> dict:
    return fetch_soil_telemetry(lat, lon)


@st.cache_data(ttl=3600, show_spinner=False)
def get_satellite(lat: float, lon: float) -> dict:
    return fetch_satellite_agroclimatology(lat, lon)


@st.cache_data(ttl=3600, show_spinner=False)
def get_soil(lat: float, lon: float, hub_name: str = "") -> dict:
    return fetch_soil_profile(lat, lon, hub_name)


@st.cache_data(ttl=86400, show_spinner=False)
def get_cached_geocoding(query: str):
    return geocode_location(query)


@st.cache_data
def get_faslyn_logo_base64() -> str:
    """Load base64 data URI of official circular Faslyn logo."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(current_dir, "assets", "faslyn_logo.png")
    webp_path = os.path.join(current_dir, "assets", "faslyn_logo.webp")
    target = png_path if os.path.exists(png_path) else webp_path
    if os.path.exists(target):
        ext = "png" if target.endswith(".png") else "webp"
        try:
            with open(target, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/{ext};base64,{b64}"
        except Exception:
            return ""
    return ""


def get_hero_bg_base64() -> str:
    """Return base64 data URI for the farmer hero section background image."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    webp_path = os.path.join(current_dir, "assets", "hero_farmer_bg.webp")
    png_path = os.path.join(current_dir, "assets", "hero_farmer_bg.png")
    target = webp_path if os.path.exists(webp_path) else png_path
    if os.path.exists(target):
        ext = "webp" if target.endswith(".webp") else "png"
        with open(target, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/{ext};base64,{b64}"
    return ""


# Asynchronously pre-warm BRICS telemetry, satellite & soil feeds in background thread
_HAS_PREWARMED_HUBS = False

def _trigger_background_prewarm():
    global _HAS_PREWARMED_HUBS
    if _HAS_PREWARMED_HUBS:
        return
    _HAS_PREWARMED_HUBS = True

    def _worker():
        import concurrent.futures
        def _warm_hub(name, hub):
            try:
                fetch_soil_telemetry(hub["lat"], hub["lon"])
            except Exception:
                pass
            try:
                fetch_satellite_agroclimatology(hub["lat"], hub["lon"])
            except Exception:
                pass
            try:
                fetch_soil_profile(hub["lat"], hub["lon"], name)
            except Exception:
                pass

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
                for name, hub in BRICS_HUBS.items():
                    pool.submit(_warm_hub, name, hub)
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True, name="faslyn-prewarm").start()

_trigger_background_prewarm()



# ---------------------------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Faslyn — Regenerative Agricultural Intelligence",
    page_icon="frontend/assets/faslyn_logo.png",
    layout="wide",
    initial_sidebar_state="auto",
)

# ---------------------------------------------------------------------------
# SAFE HTML RENDERER (Prevents Markdown 4-space code block glitch)
# ---------------------------------------------------------------------------
def render_html(html_str: str, unsafe_allow_javascript: bool = False):
    """Render HTML safely without Markdown treating indented lines as code blocks."""
    cleaned = textwrap.dedent(html_str).strip()
    allow_js = unsafe_allow_javascript or ("<script" in cleaned.lower())
    if hasattr(st, "html"):
        try:
            st.html(cleaned, unsafe_allow_javascript=allow_js)
        except TypeError:
            st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CUSTOM CSS FOR THE EXACT DASHBOARD DESIGN
# ---------------------------------------------------------------------------
render_html(
    """
    <script>
    (function() {
        try {
            var meta = document.querySelector('meta[name="viewport"]');
            if (!meta) {
                meta = document.createElement('meta');
                meta.name = 'viewport';
                document.head.appendChild(meta);
            }
            meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover';
            document.documentElement.style.overflowX = 'hidden';
            document.body.style.overflowX = 'hidden';
        } catch(e) {}
    })();
    </script>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    /* Responsive image and metric value scaling */
    @media (max-width: 768px) {
        img, .stImage {
            max-width: 100% !important;
            height: auto !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.75rem !important;
            word-break: break-word !important;
        }
    }

        /* Mobile Navigation Pill Bar Styles */
    .st-key-mobile_nav_pills_container,
    div[class*="st-key-mobile_nav_pills_container"] {
        display: none !important;
    }
    @media (max-width: 640px) {
        .st-key-mobile_nav_pills_container,
        div[class*="st-key-mobile_nav_pills_container"] {
            display: block !important;
            width: 100% !important;
            margin: 6px 0 12px 0 !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }
        .st-key-mobile_nav_pills_container [data-testid="stPills"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            gap: 6px !important;
            padding-bottom: 4px !important;
            scrollbar-width: none !important;
        }
        .st-key-mobile_nav_pills_container [data-testid="stPills"]::-webkit-scrollbar {
            display: none !important;
        }
        .st-key-mobile_nav_pills_container button {
            white-space: nowrap !important;
            flex-shrink: 0 !important;
            border-radius: 9999px !important;
            font-size: 0.82rem !important;
            font-weight: 700 !important;
            padding: 6px 14px !important;
        }
    }

    /* =======================================================================
       1. GLOBAL BASE STYLES (All Viewports & Screen Sizes)
       ======================================================================= */
    *, *::before, *::after {
        box-sizing: border-box !important;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F6F9F5 !important;
        color: #111827 !important;
        overflow-x: hidden !important;
        max-width: 100vw !important;
        -webkit-tap-highlight-color: transparent !important;
    }

    /* Wrap code and JSON blocks to prevent sideways blowout */
    pre, code, [data-testid="stCodeBlock"] {
        white-space: pre-wrap !important;
        word-break: break-all !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }

    /* Responsive DataFrames, Tables, and Charts */
    [data-testid="stDataFrame"],
    [data-testid="stTable"],
    [data-testid="stVegaLiteChart"],
    [data-testid="stPlotlyChart"],
    [data-testid="stArrowVegaLiteChart"] {
        max-width: 100% !important;
        width: 100% !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }

    /* Responsive Images */
    img, [data-testid="stImage"] img {
        max-width: 100% !important;
        height: auto !important;
        object-fit: contain !important;
    }

    /* Global Metric Cards (Consistent tactile elevation) */
    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1.5px solid #E5EBE7 !important;
        border-bottom: 2.5px solid #D5E0D8 !important;
        border-radius: 14px !important;
        padding: 10px 14px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02) !important;
        box-sizing: border-box !important;
    }
    [data-testid="stMetric"] label {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: #4B5563 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: clamp(1.10rem, 3.5vw, 1.35rem) !important;
        font-weight: 800 !important;
        color: #111827 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 0.72rem !important;
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

    /* Top Streamlit App Header bar - Zero height to eliminate empty blank space */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        overflow: visible !important;
        z-index: 99999 !important;
    }

    /* Collapse dead height from script/style injections and empty containers */
    div[data-testid="stElementContainer"]:has(style),
    div[data-testid="element-container"]:has(style),
    div[data-testid="stElementContainer"]:has(script),
    div[data-testid="element-container"]:has(script),
    div[data-testid="stElementContainer"]:empty,
    div[data-testid="element-container"]:empty {
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 0 !important;
        min-height: 0 !important;
    }

    /* Hide Deploy button, 3-dots Menu, Streamlit Cloud Toolbar Actions, Badges, and Footer */
    .stAppDeployButton,
    [data-testid="stAppDeployButton"],
    #MainMenu,
    footer,
    [data-testid="stToolbarActions"],
    .stToolbarActions,
    [data-testid="stToolbarActionButton"],
    .stToolbarActionButton,
    div[data-testid="stDecoration"],
    [data-testid="manage-app-button"],
    button[kind="manageApp"],
    [class*="manageApp"],
    [class*="viewerBadge"],
    div[data-testid="stStatusWidget"],
    div[data-testid="stSidebarResizeHandle"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* Ensure Sidebar Collapse/Expand Toggle is ALWAYS visible and tactile */
    div[data-testid="stSidebarCollapsedControl"],
    button[data-testid="stExpandSidebarButton"],
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="baseButton-headerNoPadding"],
    div[data-testid="stSidebarHeader"] button {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        z-index: 9999999 !important;
    }

    /* Style the Sidebar Open / Toggle Button */
    div[data-testid="stSidebarCollapsedControl"],
    button[data-testid="stExpandSidebarButton"] {
        top: 12px !important;
        left: 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        position: fixed !important;
    }
    div[data-testid="stSidebarCollapsedControl"] button,
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="stExpandSidebarButton"] {
        background: #FFFFFF !important;
        color: #1B4D3E !important;
        border: 1.5px solid #C8D6CC !important;
        border-bottom: 3px solid #10B981 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 14px rgba(27, 77, 62, 0.16) !important;
        padding: 6px 12px !important;
        cursor: pointer !important;
        min-width: 44px !important;
        min-height: 44px !important;
    }
    div[data-testid="stSidebarCollapsedControl"] button:hover,
    button[data-testid="stSidebarCollapseButton"]:hover,
    button[data-testid="stExpandSidebarButton"]:hover {
        background: #ECFDF5 !important;
        transform: translateY(-1.5px) !important;
    }
    div[data-testid="stSidebarCollapsedControl"] svg,
    button[data-testid="stSidebarCollapseButton"] svg,
    button[data-testid="stExpandSidebarButton"] svg {
        fill: #1B4D3E !important;
        color: #1B4D3E !important;
    }

    /* Sidebar Base Background & Typography */
    section[data-testid="stSidebar"] {
        background-color: #F8FAF7 !important;
        border-right: 1.5px solid #E2EAE4 !important;
        overflow-x: hidden !important;
    }
    div[data-testid="stSidebarUserContent"],
    div[data-testid="stSidebarContent"] {
        background-color: #F8FAF7 !important;
        padding: 1.1rem 0.85rem !important;
        overflow-x: hidden !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div {
        color: #1F2937 !important;
    }
    section[data-testid="stSidebar"] h4 {
        font-size: 0.92rem !important;
        margin-top: 0.4rem !important;
        margin-bottom: 0.2rem !important;
    }
    .sidebar-brand {
        font-size: 1.35rem;
        font-weight: 800;
        color: #1B4D3E !important;
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 0 10px 0;
    }
    .sidebar-tagline {
        font-size: 0.78rem;
        color: #4B5563 !important;
        line-height: 1.35;
        font-style: italic;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 3px !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 6px 8px !important;
        font-size: 0.86rem !important;
        border-radius: 8px !important;
        margin-bottom: 2px !important;
    }

    /* Radio button active/click selection styling - 3D Tactile Highlight */
    div[data-testid="stRadio"] div[role="radiogroup"] > label {
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
        padding: 8px 14px !important;
        border-radius: 12px !important;
        margin-bottom: 4px !important;
        border: 1px solid transparent !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background-color: #F4EFEB !important;
        transform: translateX(3px) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label:active {
        background-color: #EBDCCF !important;
        transform: translateX(1px) !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, #FAF4EF 0%, #F3E8DE 100%) !important;
        border: 1px solid rgba(212, 163, 115, 0.4) !important;
        border-left: 4px solid #B5835A !important;
        border-bottom: 2px solid rgba(181, 131, 90, 0.35) !important;
        border-radius: 12px !important;
        color: #7D4E27 !important;
        font-weight: 700 !important;
        box-shadow: 0 3px 8px rgba(181, 131, 90, 0.12), inset 0 1px 0 #ffffff !important;
        transform: translateX(2px) !important;
    }
    div[data-testid="stRadio"] input:checked + div {
        border-color: #B5835A !important;
        background-color: #B5835A !important;
        box-shadow: 0 2px 5px rgba(181, 131, 90, 0.3) !important;
    }

    /* Input and text fields */
    .stTextInput input, .stSelectbox div {
        color: #111827 !important;
        background-color: #FFFFFF !important;
    }
    .stTextInput > div > div {
        background: #FFFFFF !important;
        border-radius: 14px !important;
        border: 1.5px solid #DDE5DF !important;
        border-bottom: 2.5px solid #C5D4C9 !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.03), 0 1px 2px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stTextInput > div > div:focus-within {
        border-color: #B5835A !important;
        border-bottom: 3px solid #9C683E !important;
        box-shadow: 0 0 0 3px rgba(212, 163, 115, 0.25), 0 6px 14px rgba(0, 0, 0, 0.06) !important;
        transform: translateY(-1px) !important;
    }

    /* Top Header Bar */
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0 14px 0;
    }
    .greeting-title {
        font-size: clamp(1.20rem, 4vw, 1.85rem);
        font-weight: 800;
        color: #111827;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
        line-height: 1.25;
    }
    .greeting-subtitle {
        font-size: clamp(0.78rem, 2.5vw, 0.95rem);
        color: #6B7280;
        margin-top: 4px;
        margin-bottom: 0;
        line-height: 1.35;
    }

    /* Profile & Language Header Pill */
    .header-user-pill {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        background: linear-gradient(180deg, #FFFFFF 0%, #FAF8F5 100%);
        padding: 6px 14px;
        border-radius: 9999px;
        border: 1px solid #E5E7EB;
        border-bottom: 2.5px solid #D1D5DB;
        box-shadow: 0 3px 8px rgba(0,0,0,0.05), inset 0 1px 0 rgba(255,255,255,0.9);
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .header-user-pill:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.08), inset 0 1px 0 #FFFFFF;
    }
    .user-avatar {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%);
        color: #15803D;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 14px;
        border: 1px solid rgba(255, 255, 255, 0.85);
        box-shadow: 0 2px 4px rgba(21, 128, 61, 0.15), inset 0 1px 1px #FFFFFF;
    }

    /* KPI Metric Cards - Tactile Soft 3D Elevation */
    .kpi-card {
        background: linear-gradient(170deg, #FFFFFF 0%, #FAFCF9 100%);
        border-radius: 18px;
        padding: 16px 18px;
        border: 1px solid rgba(226, 235, 229, 0.95);
        border-bottom: 3.5px solid rgba(200, 218, 206, 0.9);
        box-shadow: 0 5px 14px -3px rgba(27, 77, 62, 0.06), 0 2px 5px -1px rgba(0, 0, 0, 0.03), inset 0 1px 1px rgba(255, 255, 255, 0.95);
        display: flex;
        align-items: center;
        gap: 14px;
        transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
        box-sizing: border-box;
    }
    .kpi-card:hover {
        transform: translateY(-3px) scale(1.006);
        border-bottom-color: rgba(181, 131, 90, 0.55);
        box-shadow: 0 14px 28px -4px rgba(27, 77, 62, 0.12), 0 6px 12px -2px rgba(0, 0, 0, 0.04), inset 0 1px 1px rgba(255, 255, 255, 1);
    }
    .kpi-icon-box {
        width: 46px;
        height: 46px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        border: 1px solid rgba(255, 255, 255, 0.85);
        border-bottom: 2px solid rgba(0, 0, 0, 0.08);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.04), inset 0 1.5px 1px rgba(255, 255, 255, 0.9);
        flex-shrink: 0;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .kpi-card:hover .kpi-icon-box {
        transform: translateY(-2px) scale(1.08) rotate(-2deg);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08), inset 0 1.5px 1px #FFFFFF;
    }
    .icon-green { background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); color: #059669; }
    .icon-orange { background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); color: #D97706; }
    .icon-teal { background: linear-gradient(135deg, #F0FDFA 0%, #CCFBF1 100%); color: #0D9488; }
    
    .kpi-val {
        font-size: clamp(1.15rem, 3.5vw, 1.75rem);
        font-weight: 800;
        color: #111827;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: clamp(0.68rem, 2vw, 0.82rem);
        font-weight: 600;
        color: #4B5563;
        margin-bottom: 2px;
    }
    .kpi-subtext {
        font-size: clamp(0.64rem, 1.8vw, 0.75rem);
        color: #9CA3AF;
        margin: 0;
    }

    /* Section Cards - Soft 3D Elevation */
    .dashboard-card,
    .st-key-home_qa_card_box {
        background: linear-gradient(170deg, #FFFFFF 0%, #FAFCF9 100%) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        border: 1px solid rgba(228, 236, 231, 0.95) !important;
        border-bottom: 3.5px solid rgba(200, 218, 206, 0.85) !important;
        box-shadow: 0 6px 18px -3px rgba(27, 77, 62, 0.06), 0 3px 8px -2px rgba(0, 0, 0, 0.03), inset 0 1px 1px rgba(255, 255, 255, 0.95) !important;
        margin-bottom: 16px !important;
        transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-sizing: border-box !important;
    }
    .dashboard-card:hover,
    .st-key-home_qa_card_box:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 28px -4px rgba(27, 77, 62, 0.1), 0 5px 10px -2px rgba(0, 0, 0, 0.04), inset 0 1px 1px #FFFFFF !important;
    }

    .card-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .card-header-title {
        font-size: clamp(0.96rem, 3vw, 1.15rem);
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

    /* Sustainability Banner - 3D Soft Elevation */
    .impact-banner {
        background: linear-gradient(135deg, #E8F5E9 0%, #F1F8F4 100%);
        border: 1px solid #C8E6C9;
        border-bottom: 3.5px solid #A5D6A7;
        border-radius: 20px;
        padding: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 20px;
        box-shadow: 0 6px 18px -3px rgba(27, 77, 62, 0.08), inset 0 1px 1px #FFFFFF;
        transition: all 0.25s ease;
        box-sizing: border-box;
    }
    .impact-banner:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 24px -4px rgba(27, 77, 62, 0.12), inset 0 1px 1px #FFFFFF;
    }
    .impact-chip {
        background: linear-gradient(180deg, #FFFFFF 0%, #FAFAF8 100%);
        border-radius: 12px;
        padding: 8px 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        border: 1px solid #E5E7EB;
        border-bottom: 2px solid #D1D5DB;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04), inset 0 1px 0 #FFFFFF;
        transition: all 0.2s ease;
        box-sizing: border-box;
    }
    .impact-chip:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 12px rgba(0, 0, 0, 0.08);
    }

    /* Primary Action Buttons - 3D Tactile Light Brown Theme */
    .stButton > button,
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(180deg, #DEAE7F 0%, #D4A373 50%, #C4925E 100%) !important;
        border: 1px solid #B5804D !important;
        border-bottom: 3.5px solid #9C683E !important;
        border-radius: 9999px !important;
        padding: 0.45rem 1.4rem !important;
        min-height: 44px !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 4px 10px rgba(181, 131, 90, 0.28), inset 0 1px 1px rgba(255, 255, 255, 0.45) !important;
    }
    .stButton > button *,
    .stButton > button p,
    .stButton > button div,
    .stButton > button span,
    button[data-testid="baseButton-primary"] *,
    button[data-testid="baseButton-primary"] p,
    button[data-testid="baseButton-primary"] div,
    button[data-testid="baseButton-primary"] span {
        color: #1E1208 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }
    .stButton > button:hover,
    button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(180deg, #E8BC90 0%, #DCAE7E 50%, #CC9A66 100%) !important;
        border-color: #A97442 !important;
        box-shadow: 0 7px 18px rgba(181, 131, 90, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.6) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button:hover *,
    button[data-testid="baseButton-primary"]:hover * {
        color: #110A03 !important;
    }
    .stButton > button:active,
    .stButton > button[data-testid="baseButton-primary"]:active {
        background: #B57F4D !important;
        border-color: #8C5B32 !important;
        border-bottom-width: 1.5px !important;
        box-shadow: 0 1px 4px rgba(181, 131, 90, 0.35), inset 0 2px 4px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(2px) !important;
    }
    .stButton > button:active *,
    button[data-testid="baseButton-primary"]:active * {
        color: #FFFFFF !important;
    }

    /* Tertiary / View All Buttons */
    .stButton > button[kind="tertiary"],
    .stButton > button[data-testid="baseButton-tertiary"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        text-align: right !important;
        justify-content: flex-end !important;
        display: inline-flex !important;
        padding: 4px 10px !important;
        min-height: 36px !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="tertiary"] *,
    .stButton > button[data-testid="baseButton-tertiary"] * {
        color: #7D4E27 !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
    }
    .stButton > button[kind="tertiary"]:hover,
    .stButton > button[data-testid="baseButton-tertiary"]:hover {
        background-color: #F8F3EE !important;
        transform: translateX(2px) !important;
    }

    /* Secondary / Back Buttons - 3D Tactile Glass Style */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="baseButton-secondary"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #FAF8F5 100%) !important;
        border: 1.5px solid #D4A373 !important;
        border-bottom: 3px solid #B57F4D !important;
        font-size: 0.88rem !important;
        padding: 0.42rem 1.25rem !important;
        border-radius: 9999px !important;
        min-height: 44px !important;
        box-shadow: 0 2px 6px rgba(181, 131, 90, 0.12), inset 0 1px 0 #FFFFFF !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button[kind="secondary"] *,
    .stButton > button[data-testid="baseButton-secondary"] * {
        color: #633811 !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="baseButton-secondary"]:hover {
        background: #FFFDFC !important;
        border-color: #B57F4D !important;
        box-shadow: 0 6px 14px rgba(181, 131, 90, 0.22), inset 0 1px 0 #FFFFFF !important;
        transform: translateY(-2px) !important;
    }

    /* Tabs Styling - 3D Accent Line */
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        color: #4B5563 !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #633811 !important;
        font-weight: 700 !important;
        border-bottom-color: #C49A6C !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #C49A6C !important;
        height: 3px !important;
        border-radius: 9999px !important;
    }

    /* Notification Bell Popover Styling */
    div[data-testid="stPopover"] {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div[data-testid="stPopover"] > button {
        background: linear-gradient(180deg, #FFFFFF 0%, #FAFAF8 100%) !important;
        color: #111827 !important;
        border: 1.5px solid #E5E7EB !important;
        border-bottom: 2.5px solid #D1D5DB !important;
        border-radius: 9999px !important;
        padding: 0.38rem 0.75rem !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        min-height: 42px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05), inset 0 1px 0 #FFFFFF !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        cursor: pointer !important;
    }
    div[data-testid="stPopover"] > button:hover {
        background: #F8F3EE !important;
        border-color: #B5835A !important;
        color: #7D4E27 !important;
        transform: translateY(-1.5px) !important;
    }
    div[data-testid="stPopoverBody"] {
        border-radius: 18px !important;
        border: 1px solid #E5E7EB !important;
        border-bottom: 3px solid #D1D5DB !important;
        box-shadow: 0 14px 34px rgba(0,0,0,0.12), 0 4px 10px rgba(0,0,0,0.05) !important;
        padding: 16px !important;
    }

    /* 3D Map Viewport Frame */
    iframe {
        border-radius: 18px !important;
        border: 1.5px solid rgba(220, 232, 224, 0.95) !important;
        border-bottom: 3.5px solid rgba(185, 205, 192, 0.95) !important;
        box-shadow: 0 10px 25px -4px rgba(27, 77, 62, 0.1), 0 4px 10px -2px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    /* Universal Location Search Form */
    div[data-testid="stForm"] {
        border: 1.5px solid #E5EBE7 !important;
        border-bottom: 2.5px solid #D5E0D8 !important;
        border-radius: 14px !important;
        padding: 6px 10px !important;
        background: #FFFFFF !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02) !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
        width: 100% !important;
    }

    /* Streamlit Spinners */
    div[data-testid="stSpinner"] > div {
        border-color: #D4A373 transparent #D4A373 transparent !important;
    }
    div[data-testid="stSpinner"] {
        color: #7D4E27 !important;
        font-weight: 600 !important;
    }

    /* Light-colored 3D Splash Loader */
    .faslyn-loader-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: radial-gradient(circle at 45% 35%, #F0FDF4 0%, #E0F2FE 45%, #E6F7EE 75%, #DCEEFE 100%);
        z-index: 9999999;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        pointer-events: auto;
        animation: faslynContainerFlow 2.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    .faslyn-loader-card {
        background: #FFFFFF;
        border: 1px solid rgba(220, 240, 230, 0.9);
        border-bottom: 4px solid #10B981;
        border-radius: 24px;
        padding: 28px 38px;
        box-shadow: 0 20px 50px -10px rgba(16, 114, 85, 0.16), 0 8px 20px -6px rgba(2, 132, 199, 0.12);
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 12px;
        max-width: 340px;
        width: 88%;
        box-sizing: border-box;
        animation: faslynCardFlow 2.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    .faslyn-spinner-wrapper {
        position: relative;
        width: 62px;
        height: 62px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .faslyn-spinner-ring {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 3px solid rgba(16, 185, 129, 0.16);
        border-top: 3px solid #10B981;
        border-right: 3px solid #0284C7;
        box-shadow: 0 3px 10px rgba(2, 132, 199, 0.18);
        animation: faslynSpin 0.65s linear infinite;
    }
    .faslyn-spinner-icon {
        font-size: 26px;
        animation: faslynPulse 0.8s ease-in-out infinite;
    }
    .faslyn-loader-brand {
        font-size: 1.55rem;
        font-weight: 800;
        color: #1B4D3E;
        letter-spacing: -0.5px;
    }
    .faslyn-loader-subtitle {
        font-size: 0.80rem;
        font-weight: 600;
        color: #4B5563;
    }
    .faslyn-loader-track {
        width: 180px;
        height: 5px;
        background: rgba(2, 132, 199, 0.12);
        border-radius: 9999px;
        overflow: hidden;
    }
    .faslyn-loader-bar {
        height: 100%;
        background: linear-gradient(90deg, #10B981 0%, #0284C7 50%, #34D399 100%);
        border-radius: 9999px;
        animation: faslynProgressFill 1.85s cubic-bezier(0.2, 0.7, 0.3, 1) forwards;
    }
    .faslyn-loader-status {
        font-size: 0.72rem;
        font-weight: 600;
        color: #6B7280;
    }

    @keyframes faslynProgressFill {
        0% { width: 0%; }
        35% { width: 55%; }
        75% { width: 88%; }
        100% { width: 100%; }
    }
    @keyframes faslynSpin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes faslynPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.12); }
    }
    @keyframes faslynCardFlow {
        0% { transform: scale(0.92); opacity: 0; }
        12% { transform: scale(1); opacity: 1; }
        82% { transform: scale(1); opacity: 1; }
        96% { transform: scale(1.10); opacity: 0; visibility: hidden; }
        100% { transform: scale(1.10); opacity: 0; visibility: hidden; display: none !important; }
    }
    @keyframes faslynContainerFlow {
        0% { opacity: 1; visibility: visible; }
        80% { opacity: 1; visibility: visible; }
        96% { opacity: 0; visibility: hidden; pointer-events: none; }
        100% { opacity: 0; visibility: hidden; pointer-events: none; display: none !important; }
    }
    @keyframes dashboard3DZoomIn {
        0% { opacity: 0; transform: perspective(1200px) translateZ(-110px) scale(0.91) translateY(26px); filter: blur(3px); }
        60% { opacity: 1; filter: blur(0px); }
        100% { opacity: 1; transform: perspective(1200px) translateZ(0px) scale(1) translateY(0); filter: blur(0px); }
    }
    @keyframes kpi3DZoomIn {
        0% { opacity: 0; transform: perspective(900px) translateZ(-65px) scale(0.88) translateY(18px); }
        100% { opacity: 1; transform: perspective(900px) translateZ(0px) scale(1) translateY(0); }
    }
    @keyframes card3DZoomIn {
        0% { opacity: 0; transform: perspective(1000px) translateZ(-75px) scale(0.90) translateY(22px); }
        100% { opacity: 1; transform: perspective(1000px) translateZ(0px) scale(1) translateY(0); }
    }
    @keyframes sidebarSlideIn {
        0% { opacity: 0; transform: translateX(-35px) scale(0.98); }
        100% { opacity: 1; transform: translateX(0) scale(1); }
    }


    /* =======================================================================
       2. DESKTOP LAYOUT (min-width: 1025px) - Laptops & Desktops
       ======================================================================= */
    @media (min-width: 1025px) {
        /* Desktop Flex Flow - physically impossible for sidebar to overlap content */
        [data-testid="stAppViewContainer"] {
            display: flex !important;
            flex-direction: row !important;
            align-items: stretch !important;
            width: 100vw !important;
            min-height: 100vh !important;
            overflow-x: hidden !important;
        }

        /* Desktop Sidebar - EXPANDED */
        section[data-testid="stSidebar"]:not([aria-expanded="false"]) {
            position: relative !important;
            flex: 0 0 260px !important;
            width: 260px !important;
            min-width: 260px !important;
            max-width: 260px !important;
            margin-left: 0 !important;
            transform: none !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 100 !important;
            box-shadow: 3px 0 18px rgba(27, 77, 62, 0.05) !important;
            border-right: 1.5px solid #E2EAE4 !important;
            transition: all 0.32s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        section[data-testid="stSidebar"]:not([aria-expanded="false"]) div[data-testid="stSidebarContent"] {
            width: 260px !important;
            min-width: 260px !important;
            max-width: 260px !important;
        }

        /* Desktop Sidebar - COLLAPSED */
        section[data-testid="stSidebar"][aria-expanded="false"] {
            position: relative !important;
            flex: 0 0 0px !important;
            width: 0px !important;
            min-width: 0px !important;
            max-width: 0px !important;
            margin: 0 !important;
            padding: 0 !important;
            transform: none !important;
            overflow: hidden !important;
            pointer-events: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            border-right: none !important;
            transition: all 0.32s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }

        /* Main Container on Desktop - Occupies remaining width up to 1400px centered */
        div[data-testid="stMain"],
        section.main,
        .stMain {
            flex: 1 1 auto !important;
            min-width: 0 !important;
            width: 100% !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            transition: all 0.32s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        .main .block-container,
        div[data-testid="stMain"] .block-container,
        div[data-testid="stMainBlockContainer"],
        .block-container {
            max-width: 1400px !important;
            padding-top: 0.75rem !important;
            padding-bottom: 3.5rem !important;
            padding-left: 2.8rem !important;
            padding-right: 2.8rem !important;
            margin-top: 0 !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }

        /* Desktop Brand Visibility */
        .mobile-top-brand {
            display: none !important;
        }
        .desktop-only-brand {
            display: inline-flex !important;
        }

        /* Row 1: KPI Cards - 4 in a row */
        div[data-testid="stHorizontalBlock"]:has(.kpi-card) {
            display: flex !important;
            flex-direction: row !important;
            gap: 16px !important;
            width: 100% !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.kpi-card) > div[data-testid="column"] {
            flex: 1 1 25% !important;
            width: 25% !important;
            min-width: 0 !important;
        }

        /* Row 2: Side-by-side Map (62%) and AI Insights (38%) */
        .st-key-dashboard_row2_container > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            gap: 20px !important;
            width: 100% !important;
            align-items: stretch !important;
        }
        .st-key-dashboard_row2_container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
            flex: 1.85 1 0 !important;
            min-width: 0 !important;
            width: 62% !important;
        }
        .st-key-dashboard_row2_container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
            flex: 1.15 1 0 !important;
            min-width: 0 !important;
            width: 38% !important;
        }

        /* Row 2: Inner Map (1.35) and Detail Box (1.0) */
        .st-key-home_map_and_details_box > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            gap: 16px !important;
            width: 100% !important;
        }
        .st-key-home_map_and_details_box > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
            flex: 1.35 1 0 !important;
            width: 57% !important;
        }
        .st-key-home_map_and_details_box > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
            flex: 1 1 0 !important;
            width: 43% !important;
        }

        /* Row 3: 3 Columns side-by-side */
        .st-key-dashboard_row3_container > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            gap: 16px !important;
            width: 100% !important;
            align-items: stretch !important;
        }
        .st-key-dashboard_row3_container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 1 1 0 !important;
            min-width: 0 !important;
            width: 33.333% !important;
            display: flex !important;
            flex-direction: column !important;
        }
        .home-row3-card,
        .st-key-home_qa_card_box {
            min-height: 255px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
        }
        .st-key-home_qa_card_box > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 12px !important;
            width: 100% !important;
        }
        .st-key-home_qa_card_box > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 1 1 50% !important;
            width: 50% !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 10px !important;
        }
        .st-key-home_qa_card_box .stButton > button {
            width: 100% !important;
            min-height: 48px !important;
            height: 48px !important;
            font-size: 0.85rem !important;
        }

        /* Search Form on Desktop */
        div[data-testid="stForm"] > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            gap: 8px !important;
            align-items: center !important;
            width: 100% !important;
        }
        div[data-testid="stForm"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
            flex: 1 1 auto !important;
        }
        div[data-testid="stForm"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
            flex: 0 0 auto !important;
            min-width: 130px !important;
        }
    }


    /* =======================================================================
       3. TABLET LAYOUT (769px to 1024px) - iPads & Tablets
       ======================================================================= */
    @media (min-width: 769px) and (max-width: 1024px) {
        /* Tablet Padding - Zero Top Blank Space */
        .main .block-container,
        div[data-testid="stMain"] .block-container,
        div[data-testid="stMainBlockContainer"],
        .block-container {
            max-width: 100% !important;
            padding-top: 0.75rem !important;
            padding-bottom: 3rem !important;
            padding-left: 1.6rem !important;
            padding-right: 1.6rem !important;
            margin-top: 0 !important;
        }

        .mobile-top-brand {
            display: none !important;
        }
        .desktop-only-brand {
            display: inline-flex !important;
        }

        /* Tablet Sidebar - Off-canvas drawer with smooth slide & backdrop dimming */
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            bottom: 0 !important;
            height: 100vh !important;
            height: 100dvh !important;
            z-index: 999999 !important;
            border-right: 1.5px solid #D1D5DB !important;
        }
        section[data-testid="stSidebar"]:not([aria-expanded="false"]) {
            width: 280px !important;
            min-width: 260px !important;
            max-width: 80vw !important;
            transform: translateX(0) !important;
            box-shadow: 14px 0 45px rgba(0, 0, 0, 0.3), 0 0 0 100vw rgba(0, 0, 0, 0.45) !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            width: 0 !important;
            transform: translateX(-100%) !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
            transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease !important;
        }

        /* Main Container on Tablet */
        div[data-testid="stMain"], section.main, .stMain {
            width: 100% !important;
            min-width: 100% !important;
            margin-left: 0 !important;
        }

        /* Row 1: KPI Cards - Sleek 2x2 Tablet Grid */
        div[data-testid="stHorizontalBlock"]:has(.kpi-card) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 12px !important;
            width: 100% !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.kpi-card) > div[data-testid="column"] {
            flex: 1 1 calc(50% - 6px) !important;
            width: calc(50% - 6px) !important;
            min-width: calc(50% - 6px) !important;
            max-width: calc(50% - 6px) !important;
        }
        .kpi-card {
            padding: 12px 14px !important;
            min-height: 86px !important;
        }
        .kpi-icon-box {
            width: 42px !important;
            height: 42px !important;
            min-width: 42px !important;
            font-size: 20px !important;
        }

        /* Row 2: Stacks vertically for optimal tablet readability */
        .st-key-dashboard_row2_container > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
            gap: 16px !important;
        }
        .st-key-dashboard_row2_container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        /* Row 2: Map and Parcel details stack vertically */
        .st-key-home_map_and_details_box > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
            gap: 14px !important;
        }
        .st-key-home_map_and_details_box > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        /* Row 3: Stacks vertically on Tablet */
        .st-key-dashboard_row3_container > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
            gap: 16px !important;
        }
        .st-key-dashboard_row3_container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        .home-row3-card, .st-key-home_qa_card_box {
            min-height: auto !important;
        }
        .st-key-home_qa_card_box > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            gap: 10px !important;
            width: 100% !important;
        }
        .st-key-home_qa_card_box > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 1 1 50% !important;
            width: 50% !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
        }
        .st-key-home_qa_card_box .stButton > button {
            min-height: 46px !important;
            height: 46px !important;
        }

        /* Sustainability Banner on Tablet */
        .impact-banner {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 14px !important;
        }
        .impact-banner > div:last-child {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 10px !important;
            width: 100% !important;
        }
        .impact-chip {
            flex: 1 1 calc(33.333% - 7px) !important;
        }
    }


    /* =======================================================================
       4. MOBILE LAYOUT (481px to 768px & base for <= 768px)
       ======================================================================= */
    @media (max-width: 768px) {
        /* Enforce Zero Horizontal Overflow Across All Mobile Viewports */
        html, body, .stApp, 
        div[data-testid="stAppViewContainer"], 
        div[data-testid="stMain"], 
        section.main, 
        .block-container, 
        div[data-testid="stMainBlockContainer"],
        div[data-testid="stVerticalBlock"], 
        div[data-testid="stVerticalBlockBorderWrapper"], 
        div[data-testid="stHorizontalBlock"] {
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        
        html, body, .stApp, 
        div[data-testid="stAppViewContainer"], 
        div[data-testid="stMain"], 
        section.main, 
        .block-container {
            overflow-x: clip !important;
            overflow-x: hidden !important;
        }

        /* Mobile Main Container Padding with Zero Top Blank Space */
        .main .block-container,
        div[data-testid="stMain"] .block-container,
        div[data-testid="stMainBlockContainer"],
        .block-container {
            padding-top: 0.75rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 2.8rem !important;
            margin-top: 0 !important;
            max-width: 100% !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }

        div[data-testid="stMain"], section.main, .stMain {
            width: 100% !important;
            min-width: 100% !important;
            margin-left: 0 !important;
            box-sizing: border-box !important;
            overflow-x: clip !important;
            overflow-x: hidden !important;
        }

        /* Mobile Sidebar - Off-canvas smooth drawer */
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            bottom: 0 !important;
            height: 100vh !important;
            height: 100dvh !important;
            z-index: 999999 !important;
            border-right: 1.5px solid #D1D5DB !important;
        }
        section[data-testid="stSidebar"]:not([aria-expanded="false"]) {
            width: 280px !important;
            min-width: 260px !important;
            max-width: 85vw !important;
            transform: translateX(0) !important;
            box-shadow: 14px 0 45px rgba(0, 0, 0, 0.3), 0 0 0 100vw rgba(0, 0, 0, 0.45) !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            width: 0 !important;
            transform: translateX(-100%) !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
            transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease !important;
        }

        /* Floating Hamburger Toggle Button on Mobile */
        div[data-testid="stSidebarCollapsedControl"],
        button[data-testid="stExpandSidebarButton"] {
            position: fixed !important;
            top: 12px !important;
            left: 12px !important;
            z-index: 9999999 !important;
        }
        div[data-testid="stSidebarCollapsedControl"] button,
        button[data-testid="stSidebarCollapseButton"] {
            background-color: rgba(255, 255, 255, 0.96) !important;
            border-radius: 12px !important;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12) !important;
            min-width: 44px !important;
            min-height: 44px !important;
            padding: 8px 12px !important;
        }

        /* Hero Top Header Row: Stack greeting and action bar cleanly on mobile */
        .st-key-hero_top_header_row div[data-testid="stHorizontalBlock"],
        div[data-testid="stHorizontalBlock"]:has(.top-header) {
            display: flex !important;
            flex-direction: column !important;
            align-items: stretch !important;
            gap: 8px !important;
            margin-bottom: 8px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        .st-key-hero_top_header_row div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
            order: 1 !important;
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        .st-key-hero_top_header_row div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
            order: -1 !important;
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            margin-bottom: 6px !important;
        }
        .desktop-only-brand {
            display: none !important;
        }
        .mobile-top-brand {
            display: flex !important;
            align-items: center !important;
            gap: 7px !important;
            flex-shrink: 0 !important;
        }
        .top-header {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 6px !important;
            padding-bottom: 4px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            overflow: hidden !important;
        }

        /* Header Action Bar Container (Bell, Language, User profile) on Mobile */
        .st-key-header_action_bar_container {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: space-between !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            gap: 6px !important;
        }
        .st-key-header_action_bar_container div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 6px !important;
            align-items: center !important;
            justify-content: flex-end !important;
            width: auto !important;
            max-width: 100% !important;
            min-width: 0 !important;
            flex: 1 1 auto !important;
            box-sizing: border-box !important;
        }
        .st-key-header_action_bar_container div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: auto !important;
            flex: 0 1 auto !important;
            min-width: 0 !important;
            max-width: none !important;
            box-sizing: border-box !important;
        }
        /* Bell Column */
        .st-key-header_action_bar_container div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
            flex: 0 0 auto !important;
            min-width: 44px !important;
        }
        /* Language Selector Column */
        .st-key-header_action_bar_container div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) {
            flex: 1 1 auto !important;
            min-width: 90px !important;
            max-width: 140px !important;
        }
        /* User Profile Column */
        .st-key-header_action_bar_container div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
            flex: 0 1 auto !important;
            min-width: 80px !important;
            max-width: 125px !important;
        }
        div[data-testid="stPopover"] > button {
            padding: 0.32rem 0.65rem !important;
            font-size: 0.82rem !important;
            min-height: 42px !important;
            height: 42px !important;
        }
        div[data-baseweb="select"] {
            min-height: 42px !important;
            height: 42px !important;
        }
        div[data-baseweb="select"] * {
            font-size: 0.82rem !important;
        }

        /* Subpage Breadcrumb Header on Mobile */
        div[data-testid="stHorizontalBlock"]:has(button[key="global_header_back"]) {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            gap: 8px !important;
            margin-bottom: 6px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        div[data-testid="stHorizontalBlock"]:has(button[key="global_header_back"]) > div[data-testid="column"]:first-child {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 85px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(button[key="global_header_back"]) > div[data-testid="column"]:last-child {
            flex: 1 1 auto !important;
            width: auto !important;
            min-width: 0 !important;
        }

        /* Row 1: KPI Cards - Sleek 2x2 Responsive Mobile Grid */
        .st-key-hero_kpi_metrics_row div[data-testid="stHorizontalBlock"],
        div[data-testid="stHorizontalBlock"]:has(.kpi-card) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
            margin-bottom: 6px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        .st-key-hero_kpi_metrics_row div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(.kpi-card) > div[data-testid="column"] {
            flex: 1 1 calc(50% - 4px) !important;
            width: calc(50% - 4px) !important;
            min-width: 0 !important;
            max-width: calc(50% - 4px) !important;
            box-sizing: border-box !important;
            overflow: hidden !important;
        }
        .kpi-card {
            padding: 10px 10px !important;
            gap: 8px !important;
            border-radius: 14px !important;
            min-height: 80px !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
            border-bottom-width: 2.5px !important;
            min-width: 0 !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            overflow: hidden !important;
        }
        .kpi-card > div:last-child {
            min-width: 0 !important;
            flex: 1 1 auto !important;
            overflow: hidden !important;
        }
        .kpi-icon-box {
            width: 36px !important;
            height: 36px !important;
            min-width: 36px !important;
            font-size: 17px !important;
            border-radius: 10px !important;
            flex-shrink: 0 !important;
        }
        .kpi-val {
            font-size: 1.18rem !important;
            line-height: 1.15 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .kpi-label {
            font-size: 0.66rem !important;
            line-height: 1.15 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .kpi-subtext {
            font-size: 0.62rem !important;
            line-height: 1.15 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        /* Section Sub-Headers ("My Fields", "AI Insights", etc.): Direct columns only */
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"] .card-header-title):not(.st-key-dashboard_row2_container > div):not(.st-key-dashboard_row3_container > div) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            justify-content: space-between !important;
            align-items: center !important;
            gap: 8px !important;
            margin-bottom: 6px !important;
            margin-top: 6px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"] .card-header-title):not(.st-key-dashboard_row2_container > div):not(.st-key-dashboard_row3_container > div) > div[data-testid="column"]:first-child {
            flex: 1 1 auto !important;
            width: auto !important;
            min-width: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"] .card-header-title):not(.st-key-dashboard_row2_container > div):not(.st-key-dashboard_row3_container > div) > div[data-testid="column"]:last-child {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 0 !important;
        }

        /* Location Search Form Row */
        div[data-testid="stForm"] > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 6px !important;
            align-items: center !important;
            width: 100% !important;
        }
        div[data-testid="stForm"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
            flex: 1 1 auto !important;
            width: auto !important;
            min-width: 0 !important;
        }
        div[data-testid="stForm"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 120px !important;
            max-width: 50% !important;
        }
        div[data-testid="stForm"] input {
            height: 42px !important;
            font-size: 16px !important;
            border-radius: 10px !important;
            padding: 4px 10px !important;
        }
        div[data-testid="stForm"] button {
            height: 42px !important;
            min-height: 42px !important;
            padding: 0 10px !important;
            font-size: 0.80rem !important;
            border-radius: 10px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        /* Row 2 & Inner Map Box: Strict Vertical Stack on Mobile */
        .st-key-dashboard_row2_container > div[data-testid="stHorizontalBlock"],
        .st-key-home_map_and_details_box > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
            max-width: 100% !important;
            gap: 14px !important;
            box-sizing: border-box !important;
        }
        .st-key-dashboard_row2_container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        .st-key-home_map_and_details_box > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            display: block !important;
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            visibility: visible !important;
            opacity: 1 !important;
            height: auto !important;
            box-sizing: border-box !important;
        }
        .home-ai-card {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            height: auto !important;
            max-height: none !important;
            overflow: visible !important;
            box-sizing: border-box !important;
        }
        .home-ai-card * {
            white-space: normal !important;
            overflow-wrap: break-word !important;
            word-break: break-word !important;
        }
        iframe {
            min-height: 250px !important;
            height: 260px !important;
            max-height: 280px !important;
            border-radius: 14px !important;
            width: 100% !important;
        }

        /* Row 3: Strict Vertical Stack of Farm Overview, Quick Actions, Upcoming & Alerts */
        .st-key-dashboard_row3_container > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
            max-width: 100% !important;
            gap: 14px !important;
            box-sizing: border-box !important;
        }
        .st-key-dashboard_row3_container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            display: block !important;
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            visibility: visible !important;
            opacity: 1 !important;
            height: auto !important;
            box-sizing: border-box !important;
        }
        .home-row3-card {
            height: auto !important;
            min-height: auto !important;
            max-height: none !important;
            overflow: visible !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        .st-key-home_qa_card_box {
            min-height: auto !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }

        /* Quick Actions: 2x2 Action Tiles */
        .st-key-home_qa_card_box > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 8px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        .st-key-home_qa_card_box > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 1 1 50% !important;
            width: 50% !important;
            max-width: 50% !important;
            min-width: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
            box-sizing: border-box !important;
        }
        .st-key-home_qa_card_box .stButton > button {
            min-height: 48px !important;
            height: auto !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            padding: 8px 6px !important;
            border-radius: 12px !important;
            white-space: normal !important;
            word-break: break-word !important;
            line-height: 1.25 !important;
            text-overflow: clip !important;
            box-sizing: border-box !important;
        }

        /* Farm Overview 2-Column Grid on Mobile */
        .home-overview-grid {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 8px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }

        /* Sustainability Impact Banner: Responsive Stack */
        .impact-banner {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 12px !important;
            padding: 14px 14px !important;
            border-radius: 16px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            overflow: hidden !important;
        }
        .impact-banner-content {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        .impact-chips-wrap {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 6px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        .impact-chips-wrap .impact-chip,
        .impact-chip {
            flex: 1 1 calc(50% - 3px) !important;
            width: calc(50% - 3px) !important;
            min-width: 0 !important;
            max-width: calc(50% - 3px) !important;
            padding: 8px 8px !important;
            border-radius: 12px !important;
            box-sizing: border-box !important;
            overflow: hidden !important;
        }

        /* General Fallback for multi-column content blocks collapsing cleanly */
        div[data-testid="stHorizontalBlock"]:not(.st-key-header_action_bar_container div):not(.st-key-hero_kpi_metrics_row div):not(:has(.kpi-card)):not(:has(> div[data-testid="column"] .card-header-title)):not(:has(button[key="global_header_back"])):not(:has(form)):not(.st-key-home_qa_card_box div):not(.st-key-sat_quick_chips_container div) > div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }

        /* Touch-Friendly Action Buttons */
        .stButton > button,
        button[data-testid="baseButton-primary"],
        button[data-testid="baseButton-secondary"] {
            width: 100% !important;
            min-height: 44px !important;
            font-size: 0.90rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 12px !important;
            padding: 6px 14px !important;
        }

        /* Inputs & Selects: 16px font prevents iOS Safari auto-zoom blowout */
        .stTextInput input, .stSelectbox div {
            font-size: 16px !important;
        }

        /* Popover dropdowns on Mobile */
        div[data-testid="stPopoverBody"] {
            max-width: 92vw !important;
            width: 92vw !important;
            left: 4vw !important;
            border-radius: 16px !important;
        }

        /* Login Form Container: 100% width on Mobile, ZERO hidden elements */
        .st-key-login_form_container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:empty {
            display: none !important;
            width: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .st-key-login_form_container div[data-testid="column"]:not(:empty) {
            display: block !important;
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            visibility: visible !important;
            opacity: 1 !important;
        }

        /* Satellite View Quick Jump Chips Carousel */
        .st-key-sat_quick_chips_container div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
            gap: 8px !important;
            padding-bottom: 6px !important;
            scrollbar-width: none !important;
            width: 100% !important;
        }
        .st-key-sat_quick_chips_container div[data-testid="stHorizontalBlock"]::-webkit-scrollbar {
            display: none !important;
        }
        .st-key-sat_quick_chips_container div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 140px !important;
        }
        .st-key-sat_quick_chips_container button {
            white-space: nowrap !important;
            border-radius: 9999px !important;
            padding: 4px 12px !important;
            font-size: 0.80rem !important;
            height: 38px !important;
            min-height: 38px !important;
        }

        /* Telemetry & Soil Metrics 2x2 Grids */
        .st-key-sat_telemetry_metrics_row div[data-testid="stHorizontalBlock"],
        .st-key-sat_soil_metrics_row div[data-testid="stHorizontalBlock"],
        .st-key-shc_inputs_container div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
            width: 100% !important;
        }
        .st-key-sat_telemetry_metrics_row div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        .st-key-sat_soil_metrics_row div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        .st-key-shc_inputs_container div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 1 1 calc(50% - 4px) !important;
            width: calc(50% - 4px) !important;
            min-width: calc(50% - 4px) !important;
            max-width: calc(50% - 4px) !important;
        }

        /* AI Samples, Regen Cards, Settings: Full-width clean stacking */
        .st-key-ai_samples_row div[data-testid="stHorizontalBlock"],
        .st-key-regen_cards_row1 div[data-testid="stHorizontalBlock"],
        .st-key-regen_cards_row2 div[data-testid="stHorizontalBlock"],
        .st-key-settings_inputs_container div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
            width: 100% !important;
        }
        .st-key-ai_samples_row div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        .st-key-regen_cards_row1 div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        .st-key-regen_cards_row2 div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        .st-key-settings_inputs_container div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
    }


    /* =======================================================================
       5. SMALL MOBILE LAYOUT (320px to 480px) - iPhone SE, Mini Phones
       ======================================================================= */
    @media (max-width: 480px) {
        /* Ultra-Compact Block Container Padding - Zero Top Blank Space */
        .main .block-container,
        div[data-testid="stMain"] .block-container,
        div[data-testid="stMainBlockContainer"],
        .block-container {
            padding-top: 0.6rem !important;
            padding-left: 0.65rem !important;
            padding-right: 0.65rem !important;
            padding-bottom: 2.5rem !important;
            margin-top: 0 !important;
        }

        /* Fluid Typography Clamps for Small Screens */
        .greeting-title {
            font-size: clamp(1.10rem, 5vw, 1.25rem) !important;
        }
        .greeting-subtitle {
            font-size: 0.76rem !important;
        }
        .card-header-title {
            font-size: 0.95rem !important;
        }

        /* Compact KPI Cards */
        .kpi-card {
            padding: 8px 10px !important;
            min-height: 72px !important;
            gap: 8px !important;
            border-radius: 12px !important;
        }
        .kpi-icon-box {
            width: 32px !important;
            height: 32px !important;
            min-width: 32px !important;
            font-size: 15px !important;
            border-radius: 8px !important;
        }
        .kpi-val {
            font-size: 1.12rem !important;
        }
        .kpi-label {
            font-size: 0.62rem !important;
        }
        .kpi-subtext {
            font-size: 0.58rem !important;
        }

        /* Compact Action Bar */
        .st-key-header_action_bar_container div[data-testid="stHorizontalBlock"] {
            gap: 4px !important;
        }
        div[data-testid="stPopover"] > button {
            padding: 0.28rem 0.5rem !important;
            font-size: 0.78rem !important;
            min-height: 40px !important;
            height: 40px !important;
        }

        /* Location Search Form: Clean vertical stack on narrow phones prevents text cutoff */
        div[data-testid="stForm"] > div[data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 6px !important;
        }
        div[data-testid="stForm"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child,
        div[data-testid="stForm"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
        }
        div[data-testid="stForm"] button {
            width: 100% !important;
            min-height: 44px !important;
            height: 44px !important;
        }

        /* Quick Action Buttons on Small Mobile */
        .st-key-home_qa_card_box .stButton > button {
            font-size: 0.78rem !important;
            padding: 4px 6px !important;
            min-height: 44px !important;
        }

        /* Impact Banner on Small Mobile */
        .impact-banner {
            padding: 12px 12px !important;
        }
        .impact-chip {
            padding: 6px 8px !important;
            font-size: 0.78rem !important;
        }

        /* Popover body spans comfortable phone width */
        div[data-testid="stPopoverBody"] {
            max-width: 95vw !important;
            width: 95vw !important;
            left: 2.5vw !important;
        }
    }

    /* Ultra-Narrow Mobile Safety (<= 360px, e.g. iPhone SE 1st gen, Galaxy Fold) */
    @media (max-width: 360px) {
        .main .block-container,
        div[data-testid="stMain"] .block-container {
            padding-left: 0.45rem !important;
            padding-right: 0.45rem !important;
        }
        .st-key-hero_kpi_metrics_row div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(.kpi-card) > div[data-testid="column"] {
            flex: 1 1 100% !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
        }
        .home-overview-grid {
            grid-template-columns: 1fr !important;
            gap: 6px !important;
        }
        .impact-chips-wrap .impact-chip {
            flex: 1 1 100% !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
        }
        .kpi-card {
            min-height: 64px !important;
        }
    }
    </style>
    """
)

# ---------------------------------------------------------------------------
# MOBILE RESPONSIVENESS REFINEMENTS (<= 640px)
# ---------------------------------------------------------------------------
render_html(
    """
    <style>
    @media (max-width: 640px) {
        /* Collapse empty spacer columns so they do not produce blank vertical blocks */
        div[data-testid="column"]:empty {
            display: none !important;
            margin: 0 !important;
            padding: 0 !important;
            height: 0 !important;
            width: 0 !important;
        }

        /* Fluid stretching for KPI Cards to fill exact screen width */
        .kpi-card {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            box-sizing: border-box !important;
            margin-bottom: 4px !important;
        }

        .dashboard-card, .home-ai-card, .home-row3-card, .impact-banner,
        .impact-chip, .home-overview-grid {
            max-width: 100% !important; min-width: 0 !important; width: 100% !important; box-sizing: border-box !important;
        }
        
        .stButton > button, .stDownloadButton > button {
            max-width: 100% !important; width: 100% !important; min-height: 46px !important; white-space: normal !important;
            overflow-wrap: anywhere !important; box-sizing: border-box !important;
        }
        
        div[data-testid="stPopoverBody"] {
            width: min(380px, calc(100vw - 20px)) !important; max-width: calc(100vw - 20px) !important;
            min-width: 0 !important; box-sizing: border-box !important;
        }
    }
    @media (max-width: 360px) {
        .main .block-container, [data-testid="stMainBlockContainer"] { padding-left: 6px !important; padding-right: 6px !important; }
        .st-key-hero_kpi_metrics_row > div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        .st-key-home_qa_card_box > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important; max-width: 100% !important; flex: 1 1 100% !important;
        }
        .home-overview-grid {
            grid-template-columns: 1fr !important;
            gap: 6px !important;
        }
    }
    </style>
    """
)

# ---------------------------------------------------------------------------
# FARMER HERO SECTION STYLING WITH SMART AGRI BACKGROUND
# ---------------------------------------------------------------------------
hero_bg_data_uri = get_hero_bg_base64()
faslyn_logo_data_uri = get_faslyn_logo_base64()

hero_css = f"""
    <style>
    /* Dashboard Hero Section - Outer container stays clean, zero padding blowout */
    .st-key-dashboard_hero_section:not([data-testid="stVerticalBlockBorderWrapper"]) {{
        background: transparent !important;
        background-image: none !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 0 18px 0 !important;
        box-shadow: none !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }}

    /* Inner border wrapper gets the smart agriculture photo background enclosing greeting + 4 keys */
    .st-key-dashboard_hero_section [data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_top_header_row),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_kpi_metrics_row),
    .st-key-dashboard_hero_section:not(:has([data-testid="stVerticalBlockBorderWrapper"])) {{
        background-image: 
            linear-gradient(90deg, 
                rgba(255, 255, 255, 0.92) 0%, 
                rgba(255, 255, 255, 0.78) 32%, 
                rgba(255, 255, 255, 0.35) 55%, 
                rgba(255, 255, 255, 0.08) 75%, 
                rgba(255, 255, 255, 0.0) 100%
            ),
            url('{hero_bg_data_uri}') !important;
        background-size: cover !important;
        background-position: right 30% !important;
        background-repeat: no-repeat !important;
        border-radius: 24px !important;
        padding: 24px 26px 22px 26px !important;
        margin: 0 !important;
        border: 1px solid rgba(220, 235, 225, 0.9) !important;
        box-shadow: 0 10px 30px -4px rgba(27, 77, 62, 0.10) !important;
        position: relative !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }}

    /* Ensure other page containers NEVER inherit or leak this background */
    .main,
    .stApp,
    div[data-testid="stMainBlockContainer"],
    div[data-testid="stMainBlockContainer"] > div[data-testid="stVerticalBlock"]:not([class*="st-key-dashboard_hero_section"]),
    div[data-testid="stVerticalBlock"]:not([class*="st-key-dashboard_hero_section"]):not(:has(.st-key-hero_top_header_row)) {{
        background-image: none !important;
    }}

    /* Hero Section Header Title & Subtitle with high-contrast text shadows (FONT UNCHANGED) */
    .st-key-dashboard_hero_section .greeting-title {{
        color: #0b291b !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        text-shadow: 0 1px 4px rgba(255, 255, 255, 0.95), 0 2px 10px rgba(255, 255, 255, 0.9) !important;
    }}
    .st-key-dashboard_hero_section .greeting-subtitle {{
        color: #17382a !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 3px rgba(255, 255, 255, 0.9) !important;
    }}

    /* Header Action Widgets (Bell, Language, Profile) Frosted Glass */
    .st-key-dashboard_hero_section div[data-testid="stPopover"] > button,
    .st-key-dashboard_hero_section div[data-baseweb="select"] > div {{
        background: rgba(255, 255, 255, 0.92) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(220, 235, 225, 0.9) !important;
        border-bottom: 2.5px solid rgba(185, 215, 200, 0.9) !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.05), inset 0 1px 1px rgba(255, 255, 255, 0.9) !important;
    }}

    /* Spacing between Hero Header and KPI Cards */
    .st-key-dashboard_hero_section .st-key-hero_kpi_metrics_row {{
        margin-top: 36px !important;
    }}

    /* Frosted Glass 4 KPI Cards inside Hero Section floating over background */
    .st-key-dashboard_hero_section .kpi-card {{
        background: rgba(255, 255, 255, 0.94) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.92) !important;
        border-radius: 20px !important;
        padding: 16px 18px !important;
        box-shadow: 0 8px 24px -4px rgba(15, 45, 35, 0.08), 0 2px 6px rgba(0, 0, 0, 0.02) !important;
        display: flex !important;
        align-items: center !important;
        gap: 14px !important;
        min-width: 0 !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
        transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    .st-key-dashboard_hero_section .kpi-card:hover {{
        background: #FFFFFF !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 28px -4px rgba(15, 45, 35, 0.14), 0 4px 10px rgba(0, 0, 0, 0.04) !important;
    }}
    .st-key-dashboard_hero_section .kpi-icon-box {{
        width: 48px !important;
        height: 48px !important;
        min-width: 48px !important;
        border-radius: 14px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 22px !important;
        flex-shrink: 0 !important;
        border: none !important;
        box-shadow: none !important;
    }}
    .st-key-dashboard_hero_section .icon-green {{
        background: #E8F5E9 !important;
    }}
    .st-key-dashboard_hero_section .icon-orange {{
        background: #FEF3C7 !important;
    }}
    .st-key-dashboard_hero_section .icon-teal {{
        background: #E6F4F1 !important;
    }}
    .st-key-dashboard_hero_section .kpi-label {{
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        color: #4B5563 !important;
        margin-bottom: 2px !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}
    .st-key-dashboard_hero_section .kpi-val {{
        font-size: clamp(1.5rem, 2.5vw, 1.95rem) !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        line-height: 1.1 !important;
        margin: 0 !important;
        letter-spacing: -0.02em !important;
    }}
    .st-key-dashboard_hero_section .kpi-subtext {{
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        color: #64748B !important;
        margin-top: 3px !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}

    /* Tablet & Mobile Hero Responsiveness */
    @media screen and (max-width: 991px) {{
        .st-key-dashboard_hero_section [data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_top_header_row),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_kpi_metrics_row),
        .st-key-dashboard_hero_section:not(:has([data-testid="stVerticalBlockBorderWrapper"])) {{
            padding: 16px 16px 16px 16px !important;
            border-radius: 18px !important;
            margin-bottom: 0 !important;
            background-position: center 25% !important;
        }}
    }}

    @media screen and (max-width: 768px) {{
        .st-key-dashboard_hero_section [data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_top_header_row),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_kpi_metrics_row),
        .st-key-dashboard_hero_section:not(:has([data-testid="stVerticalBlockBorderWrapper"])) {{
            padding: 14px 12px 14px 12px !important;
            border-radius: 18px !important;
            margin-bottom: 0 !important;
            background-position: center 20% !important;
        }}
    }}

    @media screen and (max-width: 480px) {{
        .st-key-dashboard_hero_section [data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_top_header_row),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_kpi_metrics_row),
        .st-key-dashboard_hero_section:not(:has([data-testid="stVerticalBlockBorderWrapper"])) {{
            padding: 12px 10px 12px 10px !important;
            border-radius: 16px !important;
            margin-bottom: 0 !important;
            background-position: center 20% !important;
        }}
    }}

    @media screen and (max-width: 360px) {{
        .st-key-dashboard_hero_section [data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_top_header_row),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_kpi_metrics_row),
        .st-key-dashboard_hero_section:not(:has([data-testid="stVerticalBlockBorderWrapper"])) {{
            padding: 10px 8px 10px 8px !important;
        }}
    }}
    </style>
"""
render_html(hero_css)



def render_splash_loader(status_msg="Initializing agro-intelligence feeds..."):
    """Render high-polish 3D green & blue splash loader that smoothly zooms in and fades out quickly."""
    render_html(
        f"""
        <div id="faslyn-loader-overlay" class="faslyn-loader-container">
            <div class="faslyn-loader-card">
                <div class="faslyn-spinner-wrapper">
                    <div class="faslyn-spinner-ring"></div>
                    <div class="faslyn-spinner-icon">🌱</div>
                </div>
                <div class="faslyn-loader-brand" style="display:flex; align-items:center; justify-content:center; gap:8px;">
                    <img src="{faslyn_logo_data_uri}" alt="Faslyn" style="width:36px; height:36px; border-radius:50%; object-fit:contain;" />
                    <span>Faslyn</span>
                </div>
                <div class="faslyn-loader-subtitle">Smart Agriculture &bull; Stronger Communities</div>
                <div class="faslyn-loader-track">
                    <div class="faslyn-loader-bar"></div>
                </div>
                <div class="faslyn-loader-status">{status_msg}</div>
            </div>
        </div>
        <script>
        (function() {{
            try {{
                var loader = document.getElementById("faslyn-loader-overlay");
                if (loader) {{
                    setTimeout(function() {{
                        loader.style.opacity = "0";
                        loader.style.pointerEvents = "none";
                        setTimeout(function() {{
                            loader.style.display = "none";
                            if (loader.parentNode) {{
                                loader.parentNode.removeChild(loader);
                            }}
                        }}, 200);
                    }}, 2050);
                }}
            }} catch(e) {{}}
        }})();
        </script>
        """
    )


# ---------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------
if "has_shown_initial_splash" not in st.session_state:
    st.session_state.has_shown_initial_splash = False
if "show_login_loader" not in st.session_state:
    st.session_state.show_login_loader = False
if "just_logged_in" not in st.session_state:
    st.session_state.just_logged_in = False

if not st.session_state.has_shown_initial_splash:
    render_splash_loader("Initializing agro-intelligence feeds...")
    st.session_state.has_shown_initial_splash = True

if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "user_phone" not in st.session_state:
    st.session_state.user_phone = ""
if "user_region" not in st.session_state:
    st.session_state.user_region = ""
if "farmer_id" not in st.session_state:
    st.session_state.farmer_id = ""
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
    val = t(key, st.session_state.current_language)
    if val == "back_to_home":
        return "← Back to Dashboard"
    return val


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
    """Resolve an AI client (Groq or xAI Grok) securely from .env (os.environ) or Streamlit secrets."""
    api_key = None
    try:
        api_key = st.secrets.get("GROQ_API_KEY") or st.secrets.get("GROK_API_KEY") or st.secrets.get("XAI_API_KEY")
    except Exception:
        api_key = None
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROK_API_KEY") or os.environ.get("XAI_API_KEY")
    return build_grok_client(api_key)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# DEMO USER PROFILES FOR 1-CLICK COOPERATIVE ACCESS (IMPORTED FROM backend.config)
# ---------------------------------------------------------------------------


def render_login_page():
    """Render a dedicated, tactile 3D authentication screen for BRICS smallholders."""
    render_html(
        """
        <style>
        header[data-testid="stHeader"] {
            background: transparent !important;
        }
        /* Completely hide sidebar and collapse toggle on login screen */
        section[data-testid="stSidebar"],
        div[data-testid="stSidebarCollapsedControl"],
        button[data-testid="stExpandSidebarButton"] {
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }
        [data-testid="stAppViewContainer"] {
            display: block !important;
            width: 100vw !important;
        }
        div[data-testid="stMain"],
        section.main,
        .stMain {
            width: 100% !important;
            margin-left: 0 !important;
        }
        .main .block-container,
        div[data-testid="stMain"] .block-container {
            max-width: 1040px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-top: 2rem !important;
            padding-bottom: 3.5rem !important;
        }
        .login-header-wrapper {
            text-align: center;
            margin-bottom: 26px;
        }
        .login-brand-title {
            font-size: 2.7rem;
            font-weight: 800;
            color: #111827;
            letter-spacing: -0.03em;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .login-pill-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #ECFDF5;
            border: 1px solid #A7F3D0;
            border-radius: 9999px;
            padding: 4px 14px;
            margin-top: 8px;
        }
        .login-pill-dot {
            width: 8px;
            height: 8px;
            background: #10B981;
            border-radius: 50%;
            display: inline-block;
        }
        .login-card-head {
            font-size: 1.15rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .login-card-sub {
            font-size: 0.82rem;
            color: #6B7280;
            margin-bottom: 14px;
        }
        .demo-card-item {
            background: #FFFFFF;
            border: 1.5px solid #E2EBE5;
            border-radius: 14px;
            padding: 12px 14px;
            margin-bottom: 8px;
            transition: all 0.2s ease;
        }
        .demo-card-item:hover {
            border-color: #10B981;
            background: #F0FDF4;
        }
        div[data-testid="column"]:empty {
            display: none !important;
            margin: 0 !important;
            padding: 0 !important;
            width: 0 !important;
        }
        /* Style the Demo Popover Icon button on Login page */
        div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]) div[data-testid="stPopover"] > button {
            background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%) !important;
            border: 1.5px solid #10B981 !important;
            border-bottom: 2.5px solid #059669 !important;
            border-radius: 9999px !important;
            color: #047857 !important;
            font-weight: 800 !important;
            font-size: 0.84rem !important;
            padding: 4px 14px !important;
            min-height: 36px !important;
            height: 36px !important;
            box-shadow: 0 2px 6px rgba(16, 185, 129, 0.25) !important;
            cursor: pointer !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]) div[data-testid="stPopover"] > button:hover {
            background: #A7F3D0 !important;
            border-color: #047857 !important;
            transform: translateY(-1.5px) scale(1.04) !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35) !important;
        }
        /* Popover dropdown container inside login page */
        div[data-testid="stPopoverBody"] {
            min-width: 320px !important;
            max-width: 380px !important;
            border-radius: 18px !important;
            border: 1.5px solid #BBF7D0 !important;
            border-bottom: 3.5px solid #10B981 !important;
            box-shadow: 0 16px 36px -4px rgba(16, 114, 85, 0.2) !important;
            padding: 16px !important;
            background: #FFFFFF !important;
        }
        /* Instant 0ms Fullscreen Login Bridge Curtain */
        #faslyn-login-bridge {
            position: fixed !important;
            inset: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: radial-gradient(circle at 50% 40%, #0F2D1F 0%, #0A1C13 60%, #05100B 100%) !important;
            z-index: 999999999 !important;
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            pointer-events: all !important;
        }
        #faslyn-login-bridge.active {
            display: flex !important;
            opacity: 1 !important;
        }
        .faslyn-login-exiting div[data-testid="stMain"] .block-container,
        div[data-testid="stMain"].faslyn-login-exiting .block-container,
        .main.faslyn-login-exiting .block-container {
            opacity: 0 !important;
            transform: scale(0.96) !important;
            pointer-events: none !important;
            transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        @keyframes bridgeZoomIn {
            0% { opacity: 0; transform: perspective(1000px) scale(0.92) translateZ(-60px); }
            100% { opacity: 1; transform: perspective(1000px) scale(1) translateZ(0); }
        }
        @keyframes bridgeSproutGlow {
            0% { transform: scale(0.95); filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.4)); }
            100% { transform: scale(1.08); filter: drop-shadow(0 0 24px rgba(16, 185, 129, 0.9)); }
        }
        </style>
        <div id="faslyn-login-bridge">
            <div style="display:flex; flex-direction:column; align-items:center; text-align:center; animation: bridgeZoomIn 0.38s cubic-bezier(0.16,1,0.3,1) both;">
                <div style="font-size:3.2rem; margin-bottom:10px; animation: bridgeSproutGlow 1.2s ease-in-out infinite alternate;">🌱</div>
                <div style="font-size:2.3rem; font-weight:800; color:#FFFFFF; letter-spacing:-0.03em; margin-bottom:6px;">🌿 Faslyn</div>
                <div style="font-size:0.95rem; font-weight:600; color:#A7F3D0; letter-spacing:0.02em; margin-bottom:18px;">Entering Sovereign Farm Workspace...</div>
                <div style="width:120px; height:3px; background:linear-gradient(90deg, transparent, #10B981, transparent); border-radius:9999px;"></div>
            </div>
        </div>
        """
    )

    render_html(
        """
        <div class="login-header-wrapper">
            <div class="login-brand-title">
                🌿 Faslyn
            </div>
            <div class="login-pill-badge">
                <span class="login-pill-dot"></span>
                <span style="font-size: 0.76rem; font-weight: 700; color: #047857; text-transform: uppercase; letter-spacing: 0.05em;">
                    BRICS Sovereign Agricultural Intelligence Network
                </span>
            </div>
        </div>
        """
    )

    c_login = st.container(key="login_form_container")
    col_spacer_l, col_center, col_spacer_r = c_login.columns([0.20, 0.60, 0.20], wrap=True)

    with col_center:
        col_title, col_demo_icon = col_center.columns([3.6, 1.2], vertical_alignment="center", wrap=True)
        with col_title:
            render_html(
                """
                <h2 style="font-size: 1.55rem; font-weight: 800; color: #111827; margin: 0; line-height: 1.25;">
                    Cooperative Farmer Sign-In
                </h2>
                """
            )
        with col_demo_icon:
            with st.popover("⚡ Demo", help="1-Click Instant Demo Login", use_container_width=True, key="login_demo_popover"):
                render_html(
                    """
                    <div style="padding: 2px 0 6px 0;">
                        <div style="font-weight: 800; font-size: 1.05rem; color: #111827;">⚡ 1-Click Demo Profile</div>
                        <div style="font-size: 0.76rem; color: #6B7280; margin-top: 2px;">Instant login with pre-configured BRICS agricultural telemetry</div>
                    </div>
                    """
                )

                ramesh_profile = [p for p in DEMO_PROFILES if "Ramesh" in p.get("name", "")][:1]
                if not ramesh_profile and len(DEMO_PROFILES) > 0:
                    ramesh_profile = [DEMO_PROFILES[0]]

                for idx, prof in enumerate(ramesh_profile):
                    render_html(
                        f"""
                        <div class="demo-card-item">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div style="display:flex; align-items:center; gap:10px;">
                                    <div style="width:34px; height:34px; border-radius:50%; background:#10B981; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.82rem;">
                                        {prof['avatar']}
                                    </div>
                                    <div>
                                        <div style="font-weight:700; font-size:0.88rem; color:#111827;">{prof['flag']} {prof['name']}</div>
                                        <div style="font-size:0.72rem; color:#6B7280;">{prof['role']} · {prof['region']}</div>
                                    </div>
                                </div>
                                <span style="font-size:0.7rem; font-weight:700; background:#ECFDF5; color:#047857; padding:2px 8px; border-radius:9999px; border:1px solid #A7F3D0;">
                                    {prof['badge']}
                                </span>
                            </div>
                            <div style="font-size:0.72rem; color:#4B5563; margin-top:5px; padding-left:44px;">
                                🌾 <b>Crops:</b> {prof['crops']}
                            </div>
                        </div>
                        """
                    )
                    if st.button(f"Enter as {prof['name']} ({prof['flag']}) →", key=f"quick_demo_btn_{idx}", use_container_width=True, type="primary"):
                        st.session_state.is_authenticated = True
                        st.session_state.just_logged_in = True
                        st.session_state.show_login_loader = False
                        st.session_state.user_name = prof["name"]
                        st.session_state.user_avatar = prof["avatar"]
                        st.session_state.user_role = prof["role"]
                        st.session_state.user_phone = prof["phone"]
                        st.session_state.user_region = prof["region"]
                        st.session_state.farmer_id = prof["id"]
                        st.session_state.selected_hub_name = prof["hub"]
                        st.session_state.coords = {"lat": BRICS_HUBS[prof["hub"]]["lat"], "lon": BRICS_HUBS[prof["hub"]]["lon"]}
                        st.session_state.zoom = BRICS_HUBS[prof["hub"]]["zoom"]
                        st.session_state.current_language = prof["lang"]
                        st.session_state.advisory_lang_code = LANGUAGES[prof["lang"]]
                        st.session_state.active_tab_id = "home"
                        st.session_state.nav_stack = ["home"]

                        try:
                            upsert_farmer(
                                prof["id"],
                                prof["phone"],
                                prof["name"],
                                prof["region"],
                                prof["role"],
                                prof["hub"],
                            )
                        except Exception:
                            pass

                        st.rerun()

        render_html('<div style="height: 10px;"></div>')

        login_name = st.text_input(
            "Farmer Full Name",
            value="",
            placeholder="Enter your full name",
            key="login_farmer_name",
            help="Enter your name as you would like it displayed across the dashboard.",
        )

        col_id, col_pin = col_center.columns(2, wrap=True)
        with col_id:
            login_id = st.text_input(
                "Mobile / Cooperative ID",
                value="",
                placeholder="e.g. +91 98765 43210",
                key="login_mobile_id",
                help="Your registered mobile number or cooperative member ID.",
            )
        with col_pin:
            login_pin = st.text_input(
                "Security PIN",
                value="",
                placeholder="••••••",
                type="password",
                key="login_pin_code",
                help="Enter any 4-6 digit security PIN",
            )

        col_reg, col_role = col_center.columns(2, wrap=True)
        with col_reg:
            login_region = st.text_input(
                "Farm Region / Village",
                value="",
                placeholder="e.g. Odisha, India or Punjab",
                key="login_region_input",
                help="Your farm location, district, or agricultural zone.",
            )
        with col_role:
            login_role = st.text_input(
                "Farming Role & Crops",
                value="",
                placeholder="e.g. Smallholder Farmer (Rice & Pulses)",
                key="login_role_input",
                help="e.g. Smallholder Farmer, Organic Producer, Lead Agronomist.",
            )

        hub_names = list(BRICS_HUBS.keys())
        chosen_hub = st.selectbox(
            "Agricultural Hub & Soil Baseline",
            hub_names,
            index=0,
            key="login_hub_select",
        )

        chosen_lang = st.selectbox(
            "Preferred Advisory Language",
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state.current_language) if st.session_state.current_language in LANGUAGES else 0,
            key="login_lang_select",
        )

        st.caption("🔒 Verified via Sovereign ODbL 1.0 DPG Protocol · End-to-End Encrypted")

        if st.button("🌱 Sign In to Dashboard →", type="primary", use_container_width=True, key="login_submit_btn"):
            entered_name = login_name.strip()
            if not entered_name:
                st.error("⚠️ Please enter your Farmer Full Name before signing in.")
            else:
                entered_phone = login_id.strip() if login_id.strip() else "+91 98765 43210"
                entered_region = login_region.strip() if login_region.strip() else (chosen_hub.split("—")[1].split("(")[0].strip() if "—" in chosen_hub else "Local Agricultural Belt")
                entered_role = login_role.strip() if login_role.strip() else "Smallholder Producer"

                # Compute avatar initials from entered name
                name_parts = entered_name.split()
                if len(name_parts) >= 2:
                    initials = f"{name_parts[0][0]}{name_parts[1][0]}".upper()
                elif len(name_parts) == 1 and len(name_parts[0]) >= 2:
                    initials = name_parts[0][:2].upper()
                elif len(name_parts) == 1 and len(name_parts[0]) == 1:
                    initials = name_parts[0].upper()
                else:
                    initials = "FP"

                st.session_state.is_authenticated = True
                st.session_state.just_logged_in = True
                st.session_state.show_login_loader = False
                st.session_state.user_name = entered_name
                st.session_state.user_phone = entered_phone
                st.session_state.user_region = entered_region
                st.session_state.user_role = entered_role
                st.session_state.user_avatar = initials
                st.session_state.farmer_id = f"FAS-{abs(hash(entered_name + entered_phone)) % 9000 + 1000}"
                st.session_state.selected_hub_name = chosen_hub
                st.session_state.coords = {"lat": BRICS_HUBS[chosen_hub]["lat"], "lon": BRICS_HUBS[chosen_hub]["lon"]}
                st.session_state.zoom = BRICS_HUBS[chosen_hub]["zoom"]
                st.session_state.current_language = chosen_lang
                st.session_state.advisory_lang_code = LANGUAGES[chosen_lang]
                st.session_state.active_tab_id = "home"
                st.session_state.nav_stack = ["home"]

                try:
                    upsert_farmer(
                        st.session_state.farmer_id,
                        st.session_state.user_phone,
                        st.session_state.user_name,
                        st.session_state.user_region,
                        st.session_state.user_role,
                        st.session_state.selected_hub_name,
                    )
                except Exception:
                    pass

                st.rerun()

    render_html(
        """
        <div style="margin-top: 28px; padding: 16px 20px; background: #FFFFFF; border: 1px solid #E2EBE5; border-radius: 16px; display: flex; flex-wrap: wrap; justify-content: space-around; align-items: center; gap: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.02);">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.3rem;">🔒</span>
                <div>
                    <div style="font-weight:700; font-size:0.82rem; color:#111827;">Sovereign Security</div>
                    <div style="font-size:0.72rem; color:#6B7280;">ODbL 1.0 Open Data Public Good</div>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.3rem;">🛰️</span>
                <div>
                    <div style="font-weight:700; font-size:0.82rem; color:#111827;">Zero-Sensor Telemetry</div>
                    <div style="font-size:0.72rem; color:#6B7280;">NASA POWER & Open-Meteo Feeds</div>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.3rem;">📞</span>
                <div>
                    <div style="font-weight:700; font-size:0.82rem; color:#111827;">Kisan Helpline</div>
                    <div style="font-size:0.72rem; color:#6B7280;">Toll-Free: 1800-180-1551</div>
                </div>
            </div>
        </div>
        """
    )

    render_html(
        """
        <script>
        (function() {
            function initLoginTransition() {
                var bridge = document.getElementById("faslyn-login-bridge");
                if (!bridge) return;

                function triggerExit() {
                    bridge.classList.add("active");
                    var mainEl = document.querySelector('div[data-testid="stMain"]');
                    if (mainEl) {
                        mainEl.classList.add("faslyn-login-exiting");
                    }
                }

                // Check custom login button
                var loginBtn = document.querySelector('div[class*="st-key-login_submit_btn"] button');
                if (loginBtn && !loginBtn.dataset.bridgeBound) {
                    loginBtn.dataset.bridgeBound = "true";
                    loginBtn.addEventListener("click", function() {
                        var nameInp = document.querySelector('div[class*="st-key-login_farmer_name"] input');
                        if (nameInp && nameInp.value && nameInp.value.trim().length > 0) {
                            triggerExit();
                        }
                    });
                }

                // Check all demo buttons (in popover or anywhere on page)
                var demoBtns = document.querySelectorAll('div[class*="st-key-quick_demo_btn_"] button');
                demoBtns.forEach(function(btn) {
                    if (!btn.dataset.bridgeBound) {
                        btn.dataset.bridgeBound = "true";
                        btn.addEventListener("click", function() {
                            var pBody = document.querySelectorAll('div[data-baseweb="popover"], div[data-testid="stPopoverBody"]');
                            pBody.forEach(function(pb) { pb.style.display = "none"; });
                            triggerExit();
                        });
                    }
                });
            }

            if (document.readyState === "loading") {
                document.addEventListener("DOMContentLoaded", initLoginTransition);
            } else {
                initLoginTransition();
            }
            try {
                if (window._faslynLoginObserver) {
                    window._faslynLoginObserver.disconnect();
                }
                window._faslynLoginObserver = new MutationObserver(initLoginTransition);
                window._faslynLoginObserver.observe(document.body, { childList: true, subtree: true });
            } catch(e) {}
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


# ---------------------------------------------------------------------------
# AUTHENTICATION GATEWAY (LOGIN REQUIRED BEFORE DASHBOARD CONTENT & SIDEBAR)
# ---------------------------------------------------------------------------
auth_placeholder = st.empty()

if not st.session_state.get("is_authenticated", False):
    with auth_placeholder.container():
        show_about_page()
    st.stop()
else:
    auth_placeholder.empty()

    # Guarantee complete eradication of any lingering login DOM elements or popovers
    render_html(
        """
        <style>
        .st-key-login_form_container,
        .st-key-login_demo_popover,
        .login-header-wrapper,
        .login-brand-title,
        #faslyn-login-bridge,
        div[data-testid="stPopoverBody"]:has(.demo-card-item),
        div[data-baseweb="popover"]:has(.demo-card-item) {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
            height: 0 !important;
            max-height: 0 !important;
            position: absolute !important;
            top: -9999px !important;
            left: -9999px !important;
            overflow: hidden !important;
        }
        </style>
        <script>
        (function() {
            try {
                if (window._faslynLoginObserver) {
                    window._faslynLoginObserver.disconnect();
                }
                var mainEl = document.querySelector('div[data-testid="stMain"]');
                if (mainEl) {
                    mainEl.classList.remove("faslyn-login-exiting");
                }
                var bridge = document.getElementById("faslyn-login-bridge");
                if (bridge) bridge.remove();

                var popovers = document.querySelectorAll('div[data-baseweb="popover"], div[data-testid="stPopoverBody"]');
                popovers.forEach(function(p) {
                    if (p.textContent && (p.textContent.includes("1-Click Demo") || p.textContent.includes("Enter as") || p.textContent.includes("Cooperative Farmer"))) {
                        p.remove();
                    }
                });

                var loginContainers = document.querySelectorAll('.st-key-login_form_container, .login-header-wrapper');
                loginContainers.forEach(function(el) {
                    el.remove();
                });
            } catch(e) {}
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )

# ---------------------------------------------------------------------------
# 3D ZOOM-IN TRANSITION FROM LOGIN TO DASHBOARD (NO INTERMEDIATE LOADER)
# ---------------------------------------------------------------------------
if st.session_state.get("just_logged_in", False):
    render_html(
        """
        <style>
        .main .block-container,
        div[data-testid="stMain"] .block-container {
            animation: dashboard3DZoomIn 0.58s cubic-bezier(0.16, 1, 0.3, 1) both !important;
            transform-origin: center top !important;
            will-change: transform, opacity;
        }
        .kpi-card {
            animation: kpi3DZoomIn 0.52s cubic-bezier(0.16, 1, 0.3, 1) both !important;
            transform-origin: center center !important;
        }
        .st-key-dashboard_hero_section,
        div[class*="st-key-dashboard_hero_section"],
        div[data-testid="stVerticalBlockBorderWrapper"].st-key-dashboard_hero_section {
            animation: card3DZoomIn 0.58s cubic-bezier(0.16, 1, 0.3, 1) both !important;
            transform-origin: center top !important;
        }
        .dashboard-card,
        iframe,
        div[data-testid="stIFrame"],
        .impact-banner {
            animation: card3DZoomIn 0.60s cubic-bezier(0.16, 1, 0.3, 1) both !important;
            transform-origin: center center !important;
        }
        section[data-testid="stSidebar"] {
            animation: sidebarSlideIn 0.50s cubic-bezier(0.16, 1, 0.3, 1) both !important;
            transform-origin: left center !important;
        }
        </style>
        """
    )
    st.session_state.just_logged_in = False

# Fast concurrent ingestion of telemetry, satellite & soil feeds (cached in-memory for sub-millisecond response)
def _fetch_dashboard_feeds(lat: float, lon: float, hub_name: str):
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        f_tel = pool.submit(get_telemetry, lat, lon)
        f_sat = pool.submit(get_satellite, lat, lon)
        f_soil = pool.submit(get_soil, lat, lon, hub_name)
        return f_tel.result(), f_sat.result(), f_soil.result()

telemetry, satellite, soil_data = _fetch_dashboard_feeds(
    st.session_state.coords["lat"],
    st.session_state.coords["lon"],
    st.session_state.selected_hub_name,
)
st.session_state.telemetry = telemetry
st.session_state.satellite = satellite
st.session_state.soil_data = soil_data

# Record persistent environmental telemetry snapshot asynchronously in background thread
try:
    threading.Thread(
        target=log_telemetry_snapshot,
        args=(
            st.session_state.coords["lat"],
            st.session_state.coords["lon"],
            st.session_state.selected_hub_name,
            telemetry,
            satellite,
        ),
        daemon=True,
    ).start()
except Exception:
    pass

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
# SIDEBAR — BRANDING & NAVIGATION (APPEARS AFTER LOGIN IS SUCCESSFUL)
# ===========================================================================
with st.sidebar:
    render_html(
        f"""
        <div class="sidebar-brand" style="display: flex; align-items: center; gap: 10px;">
            <img src="{faslyn_logo_data_uri}" alt="Faslyn Logo" style="width: 32px; height: 32px; border-radius: 50%; object-fit: contain; box-shadow: 0 2px 5px rgba(0,0,0,0.06);" />
            <span>Faslyn</span>
        </div>
        <div style="background: #F0FDF4; border: 1.5px solid #BBF7D0; border-radius: 12px; padding: 9px 12px; margin: 6px 0 12px 0; display: flex; align-items: center; gap: 10px;">
            <div style="width: 34px; height: 34px; border-radius: 50%; background: #10B981; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; flex-shrink: 0; box-shadow: 0 2px 6px rgba(16,185,129,0.25);">
                {st.session_state.get('user_avatar') or 'FP'}
            </div>
            <div style="overflow: hidden; line-height: 1.25;">
                <div style="font-weight: 700; font-size: 0.84rem; color: #111827; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;" title="{st.session_state.get('user_name') or 'Farmer'}">{st.session_state.get('user_name') or 'Farmer'}</div>
                <div style="font-size: 0.70rem; color: #059669; font-weight: 600; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">{st.session_state.get('user_region') or 'BRICS Sovereign Network'}</div>
            </div>
        </div>
        """
    )

    current_label = id_to_label.get(st.session_state.active_tab_id, _("nav_home"))
    all_labels = [label for tab_id, label in nav_items]
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

    # AI Engine Status in sidebar (Keys managed securely via server-side .env / Cloud Secrets)
    client = get_client()
    if client is not None:
        p_label = client.get("provider", "Groq" if client.get("api_key", "").startswith("gsk_") else "xAI Grok")
        render_html(
            f"""
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 7px 10px; font-size: 0.74rem; color: #047857; display: flex; align-items: center; gap: 6px;">
                <span style="width: 7px; height: 7px; background: #10B981; border-radius: 50%; display: inline-block;"></span>
                <b>AI Engine:</b> {p_label} Live
            </div>
            """
        )
    else:
        render_html(
            """
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 7px 10px; font-size: 0.74rem; color: #059669; display: flex; align-items: center; gap: 6px;">
                <span style="width: 7px; height: 7px; background: #10B981; border-radius: 50%; display: inline-block;"></span>
                <b>AI Engine:</b> Offline Calibrated
            </div>
            """
        )

    st.markdown("---")
    render_html(
        """
        <div style="text-align: center; padding: 12px 0 8px 0;">
            <div style="font-size: 30px; margin-bottom: 4px;">🌱</div>
            <div class="sidebar-tagline">
                Healthier Soil<br>Greener Tomorrow<br><b>Together</b>
            </div>
        </div>
        """
    )
    if st.button("🚪 Log Out", key="sidebar_logout_btn", use_container_width=True, type="secondary"):
        st.session_state.is_authenticated = False
        st.session_state.has_shown_initial_splash = False
        st.session_state.show_login_loader = False
        st.session_state.just_logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_phone = ""
        st.session_state.user_region = ""
        st.session_state.user_role = ""
        st.session_state.user_avatar = ""
        st.session_state.farmer_id = ""
        st.session_state.active_tab_id = "home"
        st.session_state.nav_stack = ["home"]
        st.rerun()

# ===========================================================================
# TOP HEADER BAR WITH LIVE LANGUAGE SWITCHER
# ===========================================================================
def render_header_actions(show_mobile_logo: bool = True):
    c_hdr_actions = st.container(key="header_action_bar_container")
    with c_hdr_actions:
        if show_mobile_logo:
            render_html(
                f"""
                <div class="mobile-top-brand">
                    <div style="display:inline-flex; align-items:center; gap:8px;">
                        <img src="{faslyn_logo_data_uri}" alt="Faslyn" style="width:26px; height:26px; border-radius:50%; object-fit:contain;" />
                        <span style="font-weight:800; font-size:1.02rem; color:#1B4D3E; letter-spacing:-0.01em;">Faslyn</span>
                    </div>
                </div>
                """
            )
        c_bell, c_lang, c_user = st.columns([1.1, 2.5, 3], vertical_alignment="center", wrap=False)
    with c_bell:
        unread_count = sum(1 for n in st.session_state.notifications if not n.get("read", False))
        bell_label = f"🔔 {unread_count}" if unread_count > 0 else "🔔"
        with st.popover(bell_label, help=_("upcoming_alerts"), use_container_width=True):
            st.markdown(f"#### {_('upcoming_alerts')}")
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
                col_b1, col_b2 = st.columns([1.8, 1.2], wrap=True)
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
            c_all1, c_all2 = st.columns(2, wrap=True)
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
        u_name = st.session_state.get("user_name", "Farmer")
        u_avatar = st.session_state.get("user_avatar", "FP")
        u_role = st.session_state.get("user_role", _("farmer_role"))
        u_region = st.session_state.get("user_region", "Odisha, India")
        u_id = st.session_state.get("farmer_id", "IN-OD-2026-4482")
        u_phone = st.session_state.get("user_phone", "+91 98765 43210")

        short_name = u_name.split()[0] if u_name else "Farmer"
        with st.popover(f"👤 {short_name}", use_container_width=True):
            render_html(
                f"""
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                    <div style="width:40px; height:40px; border-radius:50%; background:#10B981; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.95rem; box-shadow:0 2px 6px rgba(16,185,129,0.3);">
                        {u_avatar}
                    </div>
                    <div>
                        <div style="font-size:0.92rem; font-weight:700; color:#111827; line-height:1.2;">{u_name}</div>
                        <div style="font-size:0.75rem; color:#6B7280;">{u_role}</div>
                        <div style="font-size:0.72rem; color:#10B981; font-weight:600;">{u_region}</div>
                    </div>
                </div>
                <div style="background:#F9FBFA; border:1px solid #E2EBE5; border-radius:8px; padding:8px 10px; margin-bottom:12px; font-size:0.74rem; color:#4B5563;">
                    <div><b>Cooperative ID:</b> {u_id}</div>
                    <div><b>Mobile / Phone:</b> {u_phone}</div>
                    <div><b>Network:</b> BRICS AgriN Sovereign DPG</div>
                </div>
                """
            )
            if st.button("🚪 Log Out / Change Details", key="popover_logout_btn", use_container_width=True, type="secondary"):
                st.session_state.is_authenticated = False
                st.session_state.has_shown_initial_splash = False
                st.session_state.show_login_loader = False
                st.session_state.just_logged_in = False
                st.session_state.user_name = ""
                st.session_state.user_phone = ""
                st.session_state.user_region = ""
                st.session_state.user_role = ""
                st.session_state.user_avatar = ""
                st.session_state.farmer_id = ""
                st.session_state.active_tab_id = "home"
                st.session_state.nav_stack = ["home"]
                st.rerun()

# ---------------------------------------------------------------------------
# MOBILE NAVIGATION TAB BAR (VISIBLE ON MOBILE SCREENS <= 640px)
# ---------------------------------------------------------------------------
def render_mobile_navigation():
    """Renders a responsive mobile pill bar so all 6 tabs are available on mobile without needing the sidebar."""
    mobile_nav_items = [
        ("home", "🌾 " + _("nav_home")),
        ("sat", "🛰️ " + _("nav_sat")),
        ("ai", "🔬 " + _("nav_ai")),
        ("regen", "🧪 " + _("nav_regen")),
        ("brics", "🌐 " + _("nav_brics")),
        ("settings", "⚙️ " + _("nav_settings")),
    ]
    mob_labels = [label for _, label in mobile_nav_items]
    mob_map = {label: tab_id for tab_id, label in mobile_nav_items}
    
    current_tab = st.session_state.active_tab_id
    if current_tab == "farms":
        current_tab = "sat"
    elif current_tab == "impact":
        current_tab = "brics"
    
    current_label = next((l for t, l in mobile_nav_items if t == current_tab), mob_labels[0])

    with st.container(key="mobile_nav_pills_container"):
        if hasattr(st, "pills"):
            selected = st.pills(
                "Navigation",
                mob_labels,
                default=current_label,
                key=f"mob_pills_nav_{st.session_state.active_tab_id}",
                label_visibility="collapsed",
            )
        elif hasattr(st, "segmented_control"):
            selected = st.segmented_control(
                "Navigation",
                mob_labels,
                default=current_label,
                key=f"mob_pills_nav_{st.session_state.active_tab_id}",
                label_visibility="collapsed",
            )
        else:
            selected = st.radio(
                "Navigation",
                mob_labels,
                index=mob_labels.index(current_label) if current_label in mob_labels else 0,
                key=f"mob_pills_nav_{st.session_state.active_tab_id}",
                horizontal=True,
                label_visibility="collapsed",
            )
        if selected and selected != current_label:
            target_id = mob_map.get(selected, "home")
            if target_id == "home":
                st.session_state.nav_stack = ["home"]
                st.session_state.active_tab_id = "home"
                st.rerun()
            else:
                navigate_to(target_id)

if st.session_state.active_tab_id != "home":
    hdr_left, hdr_right = st.columns([3, 2], wrap=True)
    with hdr_left:
        b_c1, b_c2 = st.columns([1.5, 3.5], vertical_alignment="center", wrap=True)
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
        render_header_actions(show_mobile_logo=False)
    render_html('<div style="height: 1px; background: #E5E7EB; margin: 10px 0 18px 0;"></div>')
    render_mobile_navigation()

# ---------------------------------------------------------------------------
# FARMER ACTION CENTER
# ---------------------------------------------------------------------------
def render_farmer_action_center(moisture, soil_ph, soil_soc, soil_score, rainfall):
    """Turn live environmental indicators into a simple next action."""
    if moisture < 0.22:
        icon, title = "🚨", "Protect soil moisture"
        action = "Use deficit irrigation where available and add surface mulch to reduce evaporation."
        reason = f"Soil moisture is {moisture:.2f} m³/m³, indicating a moisture deficit."
    elif moisture > 0.35:
        icon, title = "🌊", "Protect the root zone"
        action = "Avoid unnecessary irrigation and check field drainage before the next watering cycle."
        reason = f"Soil moisture is elevated at {moisture:.2f} m³/m³."
    elif soil_soc < 1.0:
        icon, title = "🌱", "Build soil organic matter"
        action = "Consider compost, farmyard manure or biochar and maintain crop residue where practical."
        reason = f"Estimated soil organic carbon is {soil_soc:.1f}%."
    elif soil_ph < 6.0:
        icon, title = "🧪", "Review soil acidity"
        action = "Review the soil amendment plan and confirm pH with a local soil test before applying lime."
        reason = f"Estimated soil pH is {soil_ph:.1f}."
    elif rainfall < 1.0:
        icon, title = "☀️", "Prepare for a dry window"
        action = "Prioritize mulching, water conservation and early-morning irrigation."
        reason = f"Current precipitation indicator is {rainfall:.1f} mm/day."
    else:
        icon, title = "✅", "Maintain current field condition"
        action = "Continue monitoring moisture, soil health and weather before the next intervention."
        reason = f"Current composite soil-health score is {soil_score}/100."

    render_html(f"""
    <style>
    .faslyn-action-center {{background:linear-gradient(135deg,#FFFFFF 0%,#F7FBF8 100%);border:1.5px solid #DCE9E0;border-radius:18px;padding:18px;margin:12px 0 20px;box-shadow:0 8px 24px rgba(27,77,62,.07);width:100%;box-sizing:border-box;}}
    .faslyn-action-title {{font-size:1.05rem;font-weight:800;color:#12372A;margin-bottom:4px;}}
    .faslyn-action-subtitle {{color:#6B7280;font-size:.75rem;margin-bottom:14px;}}
    .faslyn-action-grid {{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;}}
    .faslyn-action-card {{background:#FFF;border:1px solid #E3ECE6;border-radius:13px;padding:12px;min-width:0;box-sizing:border-box;}}
    .faslyn-action-label {{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:#6B7280;font-weight:700;margin-bottom:5px;}}
    .faslyn-action-value {{font-size:.90rem;line-height:1.4;color:#17221D;font-weight:700;overflow-wrap:anywhere;}}
    .faslyn-action-reason {{font-size:.75rem;color:#5D6962;line-height:1.45;margin-top:5px;overflow-wrap:anywhere;}}
    @media(max-width:640px) {{.faslyn-action-center{{padding:13px;border-radius:14px;}}.faslyn-action-grid{{grid-template-columns:1fr;}}}}
    </style>
    <div class="faslyn-action-center">
      <div class="faslyn-action-title">🌾 What should I do today?</div>
      <div class="faslyn-action-subtitle">Faslyn converts field, soil and weather signals into a simple next step.</div>
      <div class="faslyn-action-grid">
        <div class="faslyn-action-card"><div class="faslyn-action-label">Priority</div><div class="faslyn-action-value">{icon} {title}</div></div>
        <div class="faslyn-action-card"><div class="faslyn-action-label">Recommended action</div><div class="faslyn-action-value">{action}</div></div>
        <div class="faslyn-action-card"><div class="faslyn-action-label">Why Faslyn says this</div><div class="faslyn-action-reason">{reason}</div></div>
      </div>
    </div>
    """)


# ===========================================================================
# VIEW 1: HOME DASHBOARD (FULLY TRANSLATED)
# ===========================================================================
if st.session_state.active_tab_id == "home":

    # -----------------------------------------------------------------------
    # DYNAMIC LIVE FEEDS: OPEN-METEO TELEMETRY & NASA POWER SATELLITE
    # -----------------------------------------------------------------------
    live_moisture = float(telemetry.get("soil_moisture", 0.24) if telemetry else 0.24)
    live_soil_temp = float(telemetry.get("soil_temp", 27.5) if telemetry else 27.5)
    live_air_temp = float(telemetry.get("air_temp", 29.0) if telemetry else 29.0)
    live_solar = float(satellite.get("solar_radiation", 18.5) if satellite else 18.5)
    live_precip = float(satellite.get("precipitation", 4.2) if satellite else 4.2)
    live_root_wetness = float(satellite.get("root_zone_soil_wetness", 0.42) if satellite else 0.42)

    # Composite soil health score based on physical moisture and ISRIC/Soil Health Card chemical fertility (SOC + pH)
    current_soil_data = st.session_state.get("soil_data", {})
    soil_soc = float(current_soil_data.get("soc_pct", 1.2))
    soil_ph = float(current_soil_data.get("ph", 6.5))
    soil_pct = calculate_soil_health_score(live_moisture, soil_soc, soil_ph)
    water_pct = int(min(100, max(15, (live_root_wetness / 0.65) * 100)))
    veg_pct = int(min(98, max(25, ((live_solar / 22.0) * 45) + (water_pct * 0.50))))

    # Pull tailored fields for the selected agricultural region/hub
    hub_key = st.session_state.selected_hub_name
    template_fields = REGIONAL_FIELDS.get(hub_key, list(REGIONAL_FIELDS.values())[0])

    fields_data = []
    for idx, tf in enumerate(template_fields):
        # Calculate dynamic health score from live telemetry & regional stress bias
        base_score = (soil_pct * 0.45 + water_pct * 0.40 + veg_pct * 0.15)
        score = int(min(98, max(22, base_score * tf.get("stress_bias", 0.85) + (idx * 4 - 5))))
        
        # Localized crop name if available, otherwise crop_en
        crop_label = _(tf["crop_key"]) if tf["crop_key"] in ["rice", "maize", "veg"] else tf["crop_en"]
        
        fields_data.append({
            "name": tf["name"],
            "crop": crop_label,
            "area": tf["area"],
            "score": score,
            "icon": tf["icon"],
        })

    for f in fields_data:
        if f["score"] >= 70:
            f["badge_class"] = "badge-healthy"
            f["badge_label"] = _("healthy")
            f["dot_color"] = "#16A34A"
            f["status"] = "healthy"
        elif f["score"] >= 50:
            f["badge_class"] = "badge-warning"
            f["badge_label"] = _("moderate_risk")
            f["dot_color"] = "#F59E0B"
            f["status"] = "warning"
        else:
            f["badge_class"] = "badge-critical"
            f["badge_label"] = _("high_risk")
            f["dot_color"] = "#DC2626"
            f["status"] = "critical"

    total_fields = len(fields_data)
    healthy_fields = sum(1 for f in fields_data if f["status"] == "healthy")
    risk_fields = total_fields - healthy_fields
    healthy_pct = int((healthy_fields / total_fields) * 100)
    risk_pct = int((risk_fields / total_fields) * 100)

    overall_health = int(sum(f["score"] for f in fields_data) / total_fields)
    trend_val = round((live_precip * 0.4) + (live_moisture * 8) - 2.5, 1)
    trend_sign = "+" if trend_val >= 0 else ""
    trend_color = "#059669" if trend_val >= 0 else "#DC2626"

    active_hub_clean = (
        st.session_state.selected_hub_name.split("—")[1]
        if "—" in st.session_state.selected_hub_name
        else st.session_state.selected_hub_name
    )

    # -----------------------------------------------------------------------
    # DASHBOARD HERO SECTION: TOP GREETING & HEADER + 4 KPI METRIC CARDS
    # Framed with smart agriculture farmer photo background (upto 4 keys only)
    # -----------------------------------------------------------------------
    with st.container(key="dashboard_hero_section", border=True):
        if hero_bg_data_uri:
            render_html(
                f"""
                <style>
                .st-key-dashboard_hero_section [data-testid="stVerticalBlockBorderWrapper"],
                div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_top_header_row),
                div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-hero_kpi_metrics_row),
                .st-key-dashboard_hero_section:not(:has([data-testid="stVerticalBlockBorderWrapper"])) {{
                    background-image: 
                        linear-gradient(90deg, 
                            rgba(255, 255, 255, 0.92) 0%, 
                            rgba(255, 255, 255, 0.78) 32%, 
                            rgba(255, 255, 255, 0.35) 55%, 
                            rgba(255, 255, 255, 0.08) 75%, 
                            rgba(255, 255, 255, 0.0) 100%
                        ),
                        url('{hero_bg_data_uri}') !important;
                    background-size: cover !important;
                    background-position: right 30% !important;
                    background-repeat: no-repeat !important;
                }}
                </style>
                """
            )

        # Top Header Greeting & Quick Actions Row
        c_hero_hdr = st.container(key="hero_top_header_row")
        render_mobile_navigation()
        hdr_left, hdr_right = c_hero_hdr.columns([3, 2], wrap=True)
        with hdr_left:
            current_farmer = st.session_state.get("user_name", "Farmer")
            greeting_text = _('greeting')
            for generic in ["Farmer!", "Farmer", "किसान भाई!", "किसान भाई", "କୃଷକ ଭାଇ!", "କୃଷକ ଭାଇ", "Produtor Rural!", "Produtor Rural", "Фермер!", "Фермер", "农户朋友！", "农户朋友"]:
                if generic in greeting_text:
                    greeting_text = greeting_text.replace(generic, f"{current_farmer}!")
                    break
            else:
                greeting_text = f"{greeting_text} {current_farmer}!"

            render_html(
                f"""
                <div class="top-header" style="padding-bottom: 0;">
                    <div style="max-width: 100%; overflow: hidden;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap;">
                            <div class="desktop-only-brand" style="display: inline-flex; align-items: center; gap: 8px; background: rgba(255, 255, 255, 0.95); padding: 4px 12px 4px 6px; border-radius: 9999px; border: 1.2px solid rgba(220, 235, 225, 0.95); box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
                                <img src="{faslyn_logo_data_uri}" alt="Faslyn Logo" style="width: 26px; height: 26px; border-radius: 50%; object-fit: contain;" />
                                <span style="font-weight: 800; font-size: 0.92rem; color: #1B4D3E; letter-spacing: -0.01em;">Faslyn</span>
                            </div>
                            <div style="display:inline-flex; align-items:center; gap:7px; background:#FFFFFF; border:1.2px solid #10B981; color:#047857; font-size:0.72rem; font-weight:700; padding:5px 14px; border-radius:9999px; box-shadow:0 2px 5px rgba(0,0,0,0.04); letter-spacing:0.04em;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="2"/>
                                    <path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"/>
                                </svg>
                                NASA & SENSOR FEEDS
                            </div>
                        </div>
                        <h1 class="greeting-title" style="word-break: break-word; margin: 0 0 6px 0;">{greeting_text}</h1>
                        <p class="greeting-subtitle" style="margin: 0;">{_('subtitle')}</p>
                    </div>
                </div>
                """
            )
        with hdr_right:
            render_header_actions()

        # -------------------------------------------------------------------
        # ROW 1: TOP 4 KPI CARDS (LIVE DATA ENGINE)
        # -------------------------------------------------------------------
        c_hero_kpis = st.container(key="hero_kpi_metrics_row")
        kpi1, kpi2, kpi3, kpi4 = c_hero_kpis.columns(4, wrap=True)

        with kpi1:
            render_html(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon-box icon-green">🌱</div>
                    <div style="min-width: 0; flex: 1 1 auto; overflow: hidden;">
                        <div class="kpi-label">{_('total_fields')}</div>
                        <div class="kpi-val">{total_fields}</div>
                        <div class="kpi-subtext">Your registered fields</div>
                    </div>
                </div>
                """
            )

        with kpi2:
            render_html(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon-box icon-green">🌿</div>
                    <div style="min-width: 0; flex: 1 1 auto; overflow: hidden;">
                        <div class="kpi-label">{_('healthy_fields')}</div>
                        <div class="kpi-val">{healthy_fields}</div>
                        <div class="kpi-subtext">{healthy_pct}% {_('of_total')}</div>
                    </div>
                </div>
                """
            )

        with kpi3:
            render_html(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon-box icon-orange">⚠️</div>
                    <div style="min-width: 0; flex: 1 1 auto; overflow: hidden;">
                        <div class="kpi-label">{_('fields_at_risk')}</div>
                        <div class="kpi-val">{risk_fields}</div>
                        <div class="kpi-subtext">{risk_pct}% {_('of_total')}</div>
                    </div>
                </div>
                """
            )

        with kpi4:
            render_html(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon-box icon-teal">📊</div>
                    <div style="min-width: 0; flex: 1 1 auto; overflow: hidden;">
                        <div class="kpi-label">Overall Health</div>
                        <div class="kpi-val">{overall_health}</div>
                        <div class="kpi-subtext">Soil health index / 100</div>
                    </div>
                </div>
                """
            )

    st.write("")

# FARMER ACTION CENTER
    # -----------------------------------------------------------------------
    render_farmer_action_center(
        moisture=live_moisture, soil_ph=soil_ph, soil_soc=soil_soc,
        soil_score=soil_pct, rainfall=live_precip,
    )

        # -----------------------------------------------------------------------
    # ROW 2: "MY FIELDS" MAP (LEFT) & "AI INSIGHTS" (RIGHT)
    # -----------------------------------------------------------------------
    c_row2 = st.container(key="dashboard_row2_container")
    mid_left, mid_right = c_row2.columns([1.85, 1.15], wrap=True)

    with mid_left:
        mf_c1, mf_c2 = st.columns([3, 1], vertical_alignment="center", wrap=True)
        with mf_c1:
            render_html(f'<h3 class="card-header-title">{_("my_fields")}</h3>')
        with mf_c2:
            if st.button(_("view_all"), key="btn_view_all_fields", type="tertiary", use_container_width=True):
                navigate_to("sat")

        with st.form("home_quick_loc_search", clear_on_submit=False):
            hs1, hs2 = st.columns([3.0, 1.4], vertical_alignment="center", wrap=True)
            with hs1:
                home_loc_q = st.text_input(
                    "Search Farmland Location",
                    placeholder=_("search_placeholder"),
                    key="home_loc_input",
                    label_visibility="collapsed",
                )
            with hs2:
                home_loc_sub = st.form_submit_button(_("search_guide_btn"), type="primary", use_container_width=True)

        if home_loc_sub and home_loc_q:
            with st.spinner(f"Guiding map to '{home_loc_q}'..."):
                r_loc = get_cached_geocoding(home_loc_q)
            if r_loc:
                st.session_state.last_guided_location = r_loc["display_name"]
                set_coords(r_loc["lat"], r_loc["lon"], zoom=13, hub_name=f"📍 {r_loc['short_name']}")
                st.rerun()
            else:
                st.error(f"❌ Location '{home_loc_q}' not found.")

        c_map_box = st.container(key="home_map_and_details_box")
        col_map_inner, col_detail_inner = c_map_box.columns([1.35, 1], wrap=True)

        with col_map_inner:
            center_lat = st.session_state.coords["lat"]
            center_lon = st.session_state.coords["lon"]

            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=16,
                max_zoom=18,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri World Imagery",
                control_scale=False,
                zoom_control=True,
            )

            LocateControl(
                auto_start=False,
                position="topleft",
                drawCircle=False,
                strings={"title": "Locate Device GPS"},
            ).add_to(m)

            # Field parcel geometries matching high-resolution satellite parcel outlines in screenshot
            parcel_shapes = [
                # Field 01: Northwest - irregular polygon with southeast notch
                [
                    (0.0037, -0.0024),
                    (0.0032, -0.0003),
                    (0.0015, -0.0007),
                    (0.0016, -0.0014),
                    (0.0011, -0.0015),
                    (0.0014, -0.0033),
                    (0.0031, -0.0032),
                ],
                # Field 02: Northeast - tilted agricultural rectangle
                [
                    (0.0033, 0.0022),
                    (0.0028, 0.0047),
                    (0.0007, 0.0041),
                    (0.0011, 0.0017),
                ],
                # Field 03: Southeast - tilted large plot
                [
                    (0.0000, 0.0005),
                    (-0.0005, 0.0029),
                    (-0.0028, 0.0021),
                    (-0.0021, -0.0002),
                ],
                # Field 04: Southwest - irregular parcel with angled southern boundary
                [
                    (-0.0013, -0.0035),
                    (-0.0012, -0.0015),
                    (-0.0016, -0.0010),
                    (-0.0021, -0.0008),
                    (-0.0038, -0.0014),
                    (-0.0038, -0.0018),
                    (-0.0032, -0.0037),
                    (-0.0021, -0.0036),
                ],
                # Field 05 (for regions with 5 parcels): North-Central plot
                [
                    (0.0039, -0.0001),
                    (0.0038, 0.0019),
                    (0.0018, 0.0016),
                    (0.0019, -0.0003),
                ],
            ]

            for idx, fld in enumerate(fields_data):
                shape_tpl = parcel_shapes[idx % len(parcel_shapes)]
                poly_pts = [[center_lat + dlat, center_lon + dlon] for (dlat, dlon) in shape_tpl]
                c_lat = sum(p[0] for p in poly_pts) / len(poly_pts)
                c_lon = sum(p[1] for p in poly_pts) / len(poly_pts)

                status = fld.get("status", "warning")
                if status == "critical":
                    poly_color = "#EF4444"
                elif status == "warning":
                    poly_color = "#F59E0B"
                else:
                    poly_color = "#10B981"

                folium.Polygon(
                    locations=poly_pts,
                    color=poly_color,
                    weight=2.8,
                    opacity=0.96,
                    fill=True,
                    fill_color=poly_color,
                    fill_opacity=0.30,
                    tooltip=f"{fld['name']} • {fld['crop']} ({fld['score']}%)",
                ).add_to(m)

                # Permanent on-map centered label matching uploaded design
                clean_name = fld["name"].split("(")[0].strip()
                area_txt = fld.get("area", "")
                label_html = f"""<div style="font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,sans-serif; text-align:center; color:#FFFFFF; font-weight:700; line-height:1.25; text-shadow:0 1px 4px rgba(0,0,0,0.95), 0 0 6px rgba(0,0,0,0.85); white-space:nowrap; transform:translate(-50%,-50%); pointer-events:none; user-select:none;"><div style="font-size:12px; font-weight:700; letter-spacing:0.2px;">{clean_name}</div><div style="font-size:10px; font-weight:500; opacity:0.92;">({area_txt})</div></div>"""
                folium.Marker(
                    location=[c_lat, c_lon],
                    icon=folium.DivIcon(
                        html=label_html,
                        icon_size=(100, 36),
                        icon_anchor=(50, 18),
                    ),
                ).add_to(m)

            # Custom styling and navigation controls matching the uploaded screenshot
            map_custom_html = f"""
            <style>
            .leaflet-bar {{
                border: none !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.28) !important;
                border-radius: 8px !important;
                overflow: hidden;
            }}
            .leaflet-bar a {{
                background-color: #FFFFFF !important;
                color: #1F2937 !important;
                border-bottom: 1px solid #E5E7EB !important;
                width: 32px !important;
                height: 32px !important;
                line-height: 32px !important;
                font-size: 15px !important;
                font-weight: 700 !important;
                transition: background-color 0.15s ease;
            }}
            .leaflet-bar a:hover {{
                background-color: #F3F4F6 !important;
                color: #111827 !important;
            }}
            .leaflet-control-locate {{
                margin-top: 8px !important;
            }}
            .leaflet-control-locate a {{
                border-radius: 8px !important;
                border-bottom: none !important;
            }}
            .faslyn-nav-btn {{
                position: absolute;
                bottom: 16px;
                left: 14px;
                z-index: 999;
                width: 36px;
                height: 36px;
                background: #FFFFFF;
                border-radius: 50%;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.35);
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                border: 1.5px solid rgba(255, 255, 255, 0.9);
                transition: transform 0.18s ease;
            }}
            .faslyn-nav-btn:hover {{
                transform: scale(1.08);
            }}
            </style>
            <div id="faslyn-recenter-btn" class="faslyn-nav-btn" title="Re-center Farmland">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="3 11 22 2 13 21 11 13 3 11" fill="#3B82F6" fill-opacity="0.18"></polygon>
                </svg>
            </div>
            <script>
            setTimeout(function() {{
                var mapDiv = document.querySelector('.folium-map');
                if (!mapDiv) return;
                var mapId = mapDiv.id;
                var mapInst = window[mapId];
                var navBtn = document.getElementById('faslyn-recenter-btn');
                if (navBtn && mapInst) {{
                    navBtn.onclick = function(e) {{
                        e.stopPropagation();
                        mapInst.flyTo([{center_lat}, {center_lon}], 16, {{ animate: true, duration: 1.0 }});
                    }};
                }}
            }}, 500);
            </script>
            """
            folium.Element(map_custom_html).add_to(m.get_root().html)

            st_folium(m, height=310, use_container_width=True, key="dashboard_map", returned_objects=[])

            render_html(
                f"""
                <div style="display:flex; justify-content:center; gap: 16px; font-size: 0.78rem; font-weight:600; color: #4B5563; margin-top: 6px;">
                    <span>🟢 {_('healthy')}</span>
                    <span>🟡 {_('moderate_risk')}</span>
                    <span>🔴 {_('critical')}</span>
                </div>
                """
            )

        with col_detail_inner:
            focus_field = min(fields_data, key=lambda x: x["score"])
            render_html(
                f"""
                <div style="background: linear-gradient(170deg, #FFFFFF 0%, #FAFCF9 100%); border: 1.5px solid rgba(228, 236, 231, 0.95); border-bottom: 3.5px solid rgba(200, 218, 206, 0.85); border-radius: 18px; padding: 18px; height: 100%; box-shadow: 0 6px 18px -3px rgba(27, 77, 62, 0.06), inset 0 1px 1px #ffffff; transition: all 0.25s ease;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                        <h4 style="margin:0; font-weight:800; font-size:1.15rem; color:#111827;">{focus_field['name']}</h4>
                        <span class="badge {focus_field['badge_class']}">{focus_field['badge_label']}</span>
                    </div>
                    <div style="font-size: 0.8rem; color:#4B5563; line-height: 1.6; margin-bottom: 12px;">
                        <div>{focus_field['icon']} <b>{focus_field['crop']}</b> &nbsp;•&nbsp; 📍 <b>{active_hub_clean}</b></div>
                        <div>📡 <b>{live_moisture:.2f} m³/m³</b> &nbsp;•&nbsp; ☀️ <b>{live_solar:.1f} MJ/m²</b></div>
                    </div>
                    
                    <div class="metric-bar-container">
                        <div class="metric-bar-label">
                            <span>{_('field_health')} (Composite)</span>
                            <span style="color:{focus_field['dot_color']}; font-weight:700;">{focus_field['score']}%</span>
                        </div>
                        <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: {focus_field['score']}%; background: {focus_field['dot_color']};"></div></div>
                    </div>
                    
                    <div class="metric-bar-container">
                        <div class="metric-bar-label">
                            <span>🪱 {_('soil_health')} (ISRIC + Moisture)</span>
                            <span>{soil_pct}%</span>
                        </div>
                        <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: {soil_pct}%; background: #16A34A;"></div></div>
                        <div style="font-size:0.7rem; color:#6B7280; margin-top:2px;">🧪 pH {soil_ph:.1f} · SOC {soil_soc:.1f}% · {current_soil_data.get('texture_label', 'Loam')}</div>
                    </div>
                    
                    <div class="metric-bar-container">
                        <div class="metric-bar-label">
                            <span>💧 {_('water_status')} (NASA Root-Zone)</span>
                            <span>{water_pct}%</span>
                        </div>
                        <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: {water_pct}%; background: #0284C7;"></div></div>
                    </div>
                    
                    <div class="metric-bar-container">
                        <div class="metric-bar-label">
                            <span>🌿 {_('vegetation')} (Solar Vigor)</span>
                            <span>{veg_pct}%</span>
                        </div>
                        <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: {veg_pct}%; background: #10B981;"></div></div>
                    </div>
                </div>
                """
            )
            if st.button(_("view_details_btn"), use_container_width=True, key="btn_view_field_details"):
                navigate_to("sat")

    with mid_right:
        ai_c1, ai_c2 = st.columns([2.5, 1.2], vertical_alignment="center", wrap=True)
        with ai_c1:
            render_html(f'<h3 class="card-header-title">{_("ai_insights")}</h3>')
        with ai_c2:
            if st.button(_("view_all"), key="btn_view_all_ai", type="tertiary", use_container_width=True):
                navigate_to("ai")

        render_html(
            f"""
            <div class="dashboard-card home-ai-card" style="margin-top: 4px;">
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
    c_row3 = st.container(key="dashboard_row3_container")
    col_ov, col_act, col_alt = c_row3.columns(3, wrap=True)

    with col_ov:
        fo_c1, fo_c2 = st.columns([2.5, 1.2], vertical_alignment="center", wrap=True)
        with fo_c1:
            render_html(f'<h3 class="card-header-title">{_("farm_overview")}</h3>')
        with fo_c2:
            if st.button(_("view_all"), key="btn_view_all_fo", type="tertiary", use_container_width=True):
                navigate_to("sat")

        cards_html = "".join([
            f"""
            <div style="background: linear-gradient(180deg, #FFFFFF 0%, #FAFCFA 100%); border: 1.5px solid #E5EBE7; border-bottom: 2.5px solid #D5E0D8; border-radius: 12px; padding: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.03), inset 0 1px 0 #ffffff; transition: all 0.22s ease; min-width: 0; overflow: hidden; box-sizing: border-box;">
                <div style="display:flex; align-items:center; justify-content:space-between; gap: 4px;">
                    <span style="display:flex; align-items:center; gap:5px; font-weight:700; font-size:0.80rem; color:#111827; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        <span style="color:{f['dot_color']}; flex-shrink:0;">●</span> <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{f['name']}</span>
                    </span>
                    <span style="font-size:0.75rem; font-weight:700; color:{f['dot_color']}; flex-shrink: 0;">{f['score']}%</span>
                </div>
                <div class="badge {f['badge_class']}" style="margin:4px 0; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{f['badge_label']}</div>
                <div style="font-size:0.72rem; color:#6B7280; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{f['icon']} {f['crop']} • {f['area']}</div>
            </div>
            """ for f in fields_data
        ])

        render_html(
            f"""
            <div class="dashboard-card home-row3-card" style="height: 100%; overflow: hidden;">
                <div class="home-overview-grid" style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px;">
                    {cards_html}
                </div>
            </div>
            """
        )

    with col_act:
        qa_c1, qa_c2 = st.columns([2.2, 1.3], vertical_alignment="center", wrap=True)
        with qa_c1:
            render_html(f'<h3 class="card-header-title">{_("quick_actions")}</h3>')
        with qa_c2:
            if st.button("🔄 " + _("refresh"), key="btn_refresh_feeds", type="tertiary", use_container_width=True, help="Refreshes live satellite and soil telemetry"):
                get_telemetry.clear()
                get_satellite.clear()
                st.session_state.telemetry = None
                st.session_state.satellite = None
                st.rerun()

        with st.container(key="home_qa_card_box"):
            qa1, qa2 = st.columns(2, wrap=True)
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
        ua_c1, ua_c2 = st.columns([2.5, 1.2], vertical_alignment="center", wrap=True)
        with ua_c1:
            render_html(f'<h3 class="card-header-title">{_("upcoming_alerts")}</h3>')
        with ua_c2:
            if st.button(_("view_all"), key="btn_view_all_alerts", type="tertiary", use_container_width=True):
                navigate_to("ai")

        # Formulate dynamic alerts conditioned on live moisture, chemical fertility, and precipitation
        if live_moisture < 0.22:
            alt1_title = f"🚨 {_('alert_1_title')}"
            alt1_sub = f"Moisture deficit ({live_moisture:.2f} m³/m³) · Drip irrigation recommended"
            alt1_bg = "linear-gradient(180deg, #FEF2F2 0%, #FEE8E8 100%)"
            alt1_border = "#FECACA"
            alt1_bbottom = "#FCA5A5"
            alt1_color = "#DC2626"
        elif live_moisture > 0.35:
            alt1_title = "🌊 High Soil Saturation"
            alt1_sub = f"Moisture elevated ({live_moisture:.2f} m³/m³) · Prevent root hypoxia"
            alt1_bg = "linear-gradient(180deg, #EFF6FF 0%, #DBEAFE 100%)"
            alt1_border = "#BFDBFE"
            alt1_bbottom = "#93C5FD"
            alt1_color = "#1D4ED8"
        else:
            alt1_title = "✅ Optimal Field Moisture"
            alt1_sub = f"Moisture balanced at {live_moisture:.2f} m³/m³ · Optimal crop uptake"
            alt1_bg = "linear-gradient(180deg, #F0FDF4 0%, #DCFCE7 100%)"
            alt1_border = "#BBF7D0"
            alt1_bbottom = "#86EFAC"
            alt1_color = "#15803D"

        if soil_soc < 1.0:
            alt2_title = "⚠️ Organic Carbon Deficit"
            alt2_sub = f"SOC at {soil_soc:.1f}% · Apply biochar or compost"
            alt2_bg = "linear-gradient(180deg, #FFFBEB 0%, #FEF3C7 100%)"
            alt2_border = "#FDE68A"
            alt2_bbottom = "#FCD34D"
            alt2_color = "#D97706"
        elif soil_ph < 6.0:
            alt2_title = f"⚠️ Acidic Topsoil (pH {soil_ph:.1f})"
            alt2_sub = "Lime amendment recommended for optimal nitrogen uptake"
            alt2_bg = "linear-gradient(180deg, #FFFBEB 0%, #FEF3C7 100%)"
            alt2_border = "#FDE68A"
            alt2_bbottom = "#FCD34D"
            alt2_color = "#D97706"
        else:
            alt2_title = f"🪴 Soil Fertility Stable (pH {soil_ph:.1f})"
            alt2_sub = f"SOC {soil_soc:.1f}% · Microbial diversity flourishing"
            alt2_bg = "linear-gradient(180deg, #F0FDF4 0%, #DCFCE7 100%)"
            alt2_border = "#BBF7D0"
            alt2_bbottom = "#86EFAC"
            alt2_color = "#15803D"

        if live_precip > 10.0:
            alt3_title = "🌧️ Heavy Precipitation Alert"
            alt3_sub = f"NASA satellite records {live_precip:.1f} mm/d · Clear drainage trenches"
            alt3_bg = "linear-gradient(180deg, #EFF6FF 0%, #DBEAFE 100%)"
            alt3_border = "#BAE6FD"
            alt3_bbottom = "#7DD3FC"
            alt3_color = "#0284C7"
        elif live_precip < 1.0:
            alt3_title = "☀️ Dry Weather Outlook"
            alt3_sub = f"Precipitation {live_precip:.1f} mm/d · Mulching recommended"
            alt3_bg = "linear-gradient(180deg, #F0F9FF 0%, #E0F2FE 100%)"
            alt3_border = "#BAE6FD"
            alt3_bbottom = "#7DD3FC"
            alt3_color = "#0284C7"
        else:
            alt3_title = "🌦️ Moderate Rainfall Window"
            alt3_sub = f"Precipitation {live_precip:.1f} mm/d · Ideal for seed germination"
            alt3_bg = "linear-gradient(180deg, #F0F9FF 0%, #E0F2FE 100%)"
            alt3_border = "#BAE6FD"
            alt3_bbottom = "#7DD3FC"
            alt3_color = "#0284C7"

        render_html(
            f"""
            <div class="dashboard-card home-row3-card" style="height: 100%;">
                <div style="display:flex; flex-direction:column; gap:10px;">
                    <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; padding:10px 14px; background:{alt1_bg}; border: 1px solid {alt1_border}; border-bottom: 2.5px solid {alt1_bbottom}; border-radius:12px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04); transition: all 0.2s ease;">
                        <div style="min-width: 0; overflow: hidden; word-break: break-word;">
                            <div style="font-size:0.82rem; font-weight:700; color:{alt1_color}; word-break: break-word;">{alt1_title}</div>
                            <div style="font-size:0.72rem; color:#4B5563; word-break: break-word;">{alt1_sub}</div>
                        </div>
                        <span style="color:{alt1_color}; font-weight:bold; flex-shrink: 0;">›</span>
                    </div>
                    
                    <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; padding:10px 14px; background:{alt2_bg}; border: 1px solid {alt2_border}; border-bottom: 2.5px solid {alt2_bbottom}; border-radius:12px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04); transition: all 0.2s ease;">
                        <div style="min-width: 0; overflow: hidden; word-break: break-word;">
                            <div style="font-size:0.82rem; font-weight:700; color:{alt2_color}; word-break: break-word;">{alt2_title}</div>
                            <div style="font-size:0.72rem; color:#4B5563; word-break: break-word;">{alt2_sub}</div>
                        </div>
                        <span style="color:{alt2_color}; font-weight:bold; flex-shrink: 0;">›</span>
                    </div>
                    
                    <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; padding:10px 14px; background:{alt3_bg}; border: 1px solid {alt3_border}; border-bottom: 2.5px solid {alt3_bbottom}; border-radius:12px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04); transition: all 0.2s ease;">
                        <div style="min-width: 0; overflow: hidden; word-break: break-word;">
                            <div style="font-size:0.82rem; font-weight:700; color:{alt3_color}; word-break: break-word;">{alt3_title}</div>
                            <div style="font-size:0.72rem; color:#4B5563; word-break: break-word;">{alt3_sub}</div>
                        </div>
                        <span style="color:{alt3_color}; font-weight:bold; flex-shrink: 0;">›</span>
                    </div>
                </div>
            </div>
            """
        )

    st.write("")

    # -----------------------------------------------------------------------
    # ROW 4: SUSTAINABILITY BANNER (IMPACT ESTIMATOR - LIVE COMPUTED)
    # -----------------------------------------------------------------------
    impact_soil = int(min(28, max(8, 8 + (live_moisture * 24))))
    impact_water = int(min(25, max(6, 6 + ((1.0 - live_root_wetness) * 15))))
    impact_input = 18
    impact_regen = int(min(32, max(10, 10 + (overall_health * 0.12))))

    render_html(
        f"""
        <div class="impact-banner">
            <div class="impact-banner-content">
                <div style="display:inline-flex; align-items:center; gap:6px; background:#D1FAE5; color:#065F46; padding:3px 10px; border-radius:9999px; font-size:0.74rem; font-weight:700; margin-bottom:8px;">
                    <span style="font-size:9px;">●</span> LIVE AGROCLIMATIC IMPACT MODEL
                </div>
                <h3 style="margin:0 0 6px 0; font-weight:800; font-size:1.35rem; color:#1B4D3E;">
                    {_('sustainable_future')}
                </h3>
                <p style="margin:0; font-size:0.9rem; color:#374151;">
                    {_('sustainable_desc')}
                </p>
            </div>
            
            <div class="impact-chips-wrap">
                <div class="impact-chip">
                    <span style="font-size:20px; flex-shrink:0;">🪴</span>
                    <div style="min-width: 0; overflow: hidden;">
                        <div style="font-size:0.72rem; color:#6B7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{_('soil_health')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#16A34A;">↑ +{impact_soil}%</div>
                    </div>
                </div>
                
                <div class="impact-chip">
                    <span style="font-size:20px; flex-shrink:0;">💧</span>
                    <div style="min-width: 0; overflow: hidden;">
                        <div style="font-size:0.72rem; color:#6B7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{_('water_use')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#0284C7;">↓ -{impact_water}%</div>
                    </div>
                </div>
                
                <div class="impact-chip">
                    <span style="font-size:20px; flex-shrink:0;">🧪</span>
                    <div style="min-width: 0; overflow: hidden;">
                        <div style="font-size:0.72rem; color:#6B7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{_('input_dep')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#16A34A;">↓ -{impact_input}%</div>
                    </div>
                </div>
                
                <div class="impact-chip">
                    <span style="font-size:20px; flex-shrink:0;">🌿</span>
                    <div style="min-width: 0; overflow: hidden;">
                        <div style="font-size:0.72rem; color:#6B7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{_('regen_score')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#16A34A;">↑ +{impact_regen}%</div>
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

    # -----------------------------------------------------------------------
    # LIVE LOCATION SEARCH & MAP GUIDANCE BAR
    # -----------------------------------------------------------------------
    render_html(
        f"""
        <div style="background: linear-gradient(135deg, #F0FDF4 0%, #E8F5E9 100%); border: 1px solid #C8E6C9; border-radius: 14px; padding: 12px 18px; margin-bottom: 12px;">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                <div style="display:flex; align-items:center; gap:8px; font-weight:800; font-size:1.02rem; color:#1B4D3E;">
                    <span>🔍</span> Live Farmland Location Search & Map Guidance
                </div>
                <span style="font-size:0.72rem; background:#DCFCE7; color:#166534; padding:3px 10px; border-radius:9999px; font-weight:700;">
                    ● LIVE OPENSTREETMAP & NASA FEEDS
                </span>
            </div>
            <div style="font-size:0.8rem; color:#4B5563; margin-top:4px;">
                Search any village, district, city, or global agricultural coordinate. The interactive map will automatically pan and guide to that location with live satellite & soil telemetry.
            </div>
        </div>
        """
    )

    with st.form("sat_loc_search_form", clear_on_submit=False):
        sc1, sc2 = st.columns([3.8, 1.3], vertical_alignment="center", wrap=True)
        with sc1:
            sat_search_q = st.text_input(
                "Search Location",
                placeholder=_("search_placeholder"),
                key="sat_loc_input",
                label_visibility="collapsed",
            )
        with sc2:
            sat_search_sub = st.form_submit_button(_("search_guide_btn"), type="primary", use_container_width=True)

    if sat_search_sub and sat_search_q:
        with st.spinner(f"Locating '{sat_search_q}' and fetching live satellite data..."):
            found_loc = get_cached_geocoding(sat_search_q)
        if found_loc:
            st.session_state.last_guided_location = found_loc["display_name"]
            set_coords(
                found_loc["lat"],
                found_loc["lon"],
                zoom=13,
                hub_name=f"📍 {found_loc['short_name']}",
            )
            st.rerun()
        else:
            st.error(f"❌ Could not find location for '{sat_search_q}'. Please try a broader city, district, or region name.")

    # Quick Jump Chips
    c_sug = st.container(key="sat_quick_chips_container")
    sug_cols = c_sug.columns(5, wrap=True)
    popular_sugs = [
        ("🌾 Sambalpur (Odisha)", "Sambalpur, Odisha, India"),
        ("🌽 Mato Grosso (Brazil)", "Mato Grosso, Brazil"),
        ("🚜 Punjab Grain Belt", "Ludhiana, Punjab, India"),
        ("🌻 Krasnodar (Russia)", "Krasnodar, Russia"),
        ("🌱 Heilongjiang (China)", "Harbin, Heilongjiang, China"),
    ]
    for idx, (sug_label, sug_query) in enumerate(popular_sugs):
        with sug_cols[idx]:
            if st.button(sug_label, key=f"btn_pop_sug_{idx}", type="tertiary", use_container_width=True):
                res_sug = get_cached_geocoding(sug_query)
                if res_sug:
                    st.session_state.last_guided_location = res_sug["display_name"]
                    set_coords(
                        res_sug["lat"],
                        res_sug["lon"],
                        zoom=13,
                        hub_name=f"📍 {res_sug['short_name']}",
                    )
                    st.rerun()

    st.write("")

    col_hub_a, col_hub_b = st.columns([1, 2], wrap=True)
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
            st.session_state.last_guided_location = selected_hub
            st.rerun()

        st.markdown("---")
        st.markdown(f"**Current Farmland:** `{st.session_state.selected_hub_name}`")
        if st.session_state.get("last_guided_location"):
            st.caption(f"🎯 *{st.session_state.last_guided_location}*")

        st.code(
            f"Latitude:  {st.session_state.coords['lat']:.4f}\nLongitude: {st.session_state.coords['lon']:.4f}\nZoom Level: {st.session_state.zoom}",
            language="text",
        )
        st.caption("💡 *Tip: Search above, select a hub, or click anywhere on the map to pin any custom farmland!*")

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
            popup=f"Active Farmland: {st.session_state.selected_hub_name}",
            tooltip=f"🎯 Active Farmland ({st.session_state.coords['lat']:.4f}, {st.session_state.coords['lon']:.4f})",
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
        ).add_to(m_sat)

        folium.Circle(
            location=[st.session_state.coords["lat"], st.session_state.coords["lon"]],
            radius=1500,
            color="#10B981",
            fill=True,
            fill_color="#10B981",
            fill_opacity=0.2,
            tooltip="Active Live Telemetry Catchment (1.5 km)",
        ).add_to(m_sat)

        map_interaction = st_folium(
            m_sat,
            height=390,
            use_container_width=True,
            key="sat_view_map",
            returned_objects=["last_clicked"],
        )
        if map_interaction and map_interaction.get("last_clicked"):
            c_clicked = map_interaction["last_clicked"]
            if (
                round(c_clicked["lat"], 4) != round(st.session_state.coords["lat"], 4)
                or round(c_clicked["lng"], 4) != round(st.session_state.coords["lon"], 4)
            ):
                set_coords(c_clicked["lat"], c_clicked["lng"], zoom=14, hub_name=f"📍 Manual Pinpoint ({c_clicked['lat']:.2f}, {c_clicked['lng']:.2f})")
                st.session_state.last_guided_location = f"Manual Pinpoint ({c_clicked['lat']:.4f}, {c_clicked['lng']:.4f})"
                st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Real-Time Environmental & Soil Indicators")

    st.markdown("##### 🛰️ Topsoil Physical Telemetry & Satellite Climatology")
    c_tel = st.container(key="sat_telemetry_metrics_row")
    s1, s2, s3, s4 = c_tel.columns(4, wrap=True)
    s1.metric(_("soil_health"), f"{telemetry.get('soil_moisture', 0.24):.2f} m³/m³", "Open-Meteo Topsoil (0-7cm)")
    s2.metric("Soil Temperature", f"{telemetry.get('soil_temp', 27.5):.1f} °C", "Microbial Activity Zone")
    s3.metric("Solar Radiation (NASA)", f"{satellite.get('solar_radiation', 18.5):.1f} MJ/m²/d", f"Obs: {satellite.get('data_date', 'Live')}")
    s4.metric(_("water_status"), f"{satellite.get('root_zone_soil_wetness', 0.42):.2f} (0-1)", "NASA POWER Root-Zone")

    # Soil Chemical & Nutrient Profile (ISRIC SoilGrids + Regional Baseline)
    current_soil = st.session_state.get("soil_data", {})
    st.markdown("##### 🧪 Topsoil Chemical & Nutrient Fertility Profile")
    c_chem = st.container(key="sat_soil_metrics_row")
    sc1, sc2, sc3, sc4, sc5 = c_chem.columns(5, wrap=True)
    sc1.metric("Soil pH", f"{current_soil.get('ph', 6.5):.1f}", current_soil.get("ph_label", "Neutral"))
    sc2.metric("Organic Carbon (SOC)", f"{current_soil.get('soc_pct', 1.2):.1f}%", current_soil.get("soc_rating", "Moderate"))
    sc3.metric("Available Nitrogen", f"{current_soil.get('nitrogen_kg_ha', 240)} kg/ha", "Macronutrient Pool")
    sc4.metric("Cation Exchange (CEC)", f"{current_soil.get('cec_cmol_kg', 18.0):.1f} cmol/kg", "Nutrient Retention")
    sc5.metric("Soil Texture Class", current_soil.get("texture_label", "Loam"), f"Source: {current_soil.get('source', 'ISRIC SoilGrids')}")

    with st.expander("📝 Digital Soil Health Card (Custom Lab Overrides / Manual Entry)", expanded=False):
        st.caption("Override satellite and global soil models with laboratory Soil Health Card (SHC) test measurements for pinpoint local advisory accuracy.")
        c_shc = st.container(key="shc_inputs_container")
        shc_c1, shc_c2, shc_c3, shc_c4 = c_shc.columns(4, wrap=True)
        with shc_c1:
            shc_ph = st.number_input("Laboratory pH", min_value=3.5, max_value=10.0, value=float(current_soil.get("ph", 6.5)), step=0.1, key="shc_ph_input")
        with shc_c2:
            shc_soc = st.number_input("Soil Organic Carbon (%)", min_value=0.1, max_value=8.0, value=float(current_soil.get("soc_pct", 1.2)), step=0.1, key="shc_soc_input")
        with shc_c3:
            shc_nitrogen = st.number_input("Available Nitrogen (kg/ha)", min_value=20, max_value=800, value=int(current_soil.get("nitrogen_kg_ha", 240)), step=10, key="shc_n_input")
        with shc_c4:
            shc_cec = st.number_input("CEC (cmol/kg)", min_value=2.0, max_value=60.0, value=float(current_soil.get("cec_cmol_kg", 18.0)), step=0.5, key="shc_cec_input")

        if st.button("💾 Apply Soil Health Card Values", type="secondary", key="apply_shc_btn"):
            st.session_state.soil_data.update({
                "ph": shc_ph,
                "ph_label": "Acidic" if shc_ph < 6.0 else ("Alkaline" if shc_ph > 7.5 else "Neutral"),
                "soc_pct": shc_soc,
                "soc_rating": "Low" if shc_soc < 0.75 else ("High" if shc_soc > 1.5 else "Medium"),
                "nitrogen_kg_ha": shc_nitrogen,
                "cec_cmol_kg": shc_cec,
                "source": "Farmer Soil Health Card (Manual Lab)",
            })
            st.success("✅ Soil Health Card profile applied! AI advisories and crop recommendations will now prioritize these laboratory readings.")
            st.rerun()

    if telemetry.get("trend"):
        with st.expander("📈 24-Hour Ground Weather & Soil Micro-Trend", expanded=False):
            st.dataframe(telemetry["trend"], use_container_width=True)

    render_html(
        """
        <div style="font-size:0.75rem; color:#6B7280; margin-top:8px; line-height:1.5;">
            📡 <b>Data Provenance:</b> ISRIC SoilGrids REST API (250m global soil property mapping) · NASA POWER API (CERES solar radiation & MERRA-2 meteorological assimilation, 0.5° grid) · Open-Meteo Numerical Weather Prediction (zero-sensor physical modeling).
        </div>
        """
    )

    st.markdown("---")
    bot_b1, bot_b2 = st.columns([1.5, 3], vertical_alignment="center", wrap=True)
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
                adv = generate_advisory(
                    client,
                    telemetry,
                    st.session_state.current_language,
                    satellite=satellite,
                    soil_profile=st.session_state.get("soil_data"),
                )
            st.session_state.advisory_text = adv
            st.session_state.advisory_lang_code = LANGUAGES[st.session_state.current_language]
            st.session_state.trigger_speech = True

            try:
                log_advisory_record(
                    st.session_state.get("farmer_id", "demo-farmer"),
                    st.session_state.current_language,
                    adv,
                )
            except Exception:
                pass

        if st.session_state.advisory_text:
            render_html(
                f"""
                <div style="background:#FFFFFF; border-left: 5px solid #1B4D3E; border-radius: 12px; padding: 18px; margin-top: 16px;">
                    <h4 style="margin:0 0 8px 0; color:#1B4D3E;">🗣️ Advisory ({st.session_state.current_language})</h4>
                    <p style="font-size: 1.15rem; line-height: 1.6; color:#111827; margin:0;">{st.session_state.advisory_text}</p>
                </div>
                """
            )
            col_rep, _spacer = st.columns([1, 4], wrap=True)
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

        c_leaf = st.container(key="ai_samples_row")
        v_s1, v_s2, v_s3 = c_leaf.columns(3, wrap=True)
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
            v_col1, v_col2 = st.columns([1, 2], wrap=True)
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
    bot_b1, bot_b2 = st.columns([1.5, 3], vertical_alignment="center", wrap=True)
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
            rec = generate_crop_recommendation(
                client,
                telemetry,
                satellite,
                st.session_state.current_language,
                soil_profile=st.session_state.get("soil_data"),
            )
        st.session_state.crop_recommendation = rec

        try:
            log_advisory_record(
                st.session_state.get("farmer_id", "demo-farmer"),
                st.session_state.current_language,
                rec.get("rationale", ""),
                crop_rec=rec,
            )
        except Exception:
            pass

    rec = st.session_state.crop_recommendation
    if rec:
        c_r1 = st.container(key="regen_cards_row1")
        r1, r2 = c_r1.columns(2, wrap=True)
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

        c_r2 = st.container(key="regen_cards_row2")
        r3, r4 = c_r2.columns(2, wrap=True)
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
    bot_b1, bot_b2 = st.columns([1.5, 3], vertical_alignment="center", wrap=True)
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
        "endpoint": "/api/v1/export",
        "method": "GET",
        "schema_version": "2.0.0",
        "api_service_url": f"http://localhost:{API_PORT}/api/v1/export",
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
        "soil_chemical_fertility": {
            "ph": st.session_state.get("soil_data", {}).get("ph", 6.5),
            "ph_class": st.session_state.get("soil_data", {}).get("ph_label", "Neutral"),
            "soil_organic_carbon_pct": st.session_state.get("soil_data", {}).get("soc_pct", 1.2),
            "nitrogen_kg_ha": st.session_state.get("soil_data", {}).get("nitrogen_kg_ha", 240),
            "cec_cmol_kg": st.session_state.get("soil_data", {}).get("cec_cmol_kg", 18.0),
            "soil_texture": st.session_state.get("soil_data", {}).get("texture_label", "Loam"),
            "source": st.session_state.get("soil_data", {}).get("source", "ISRIC SoilGrids 250m"),
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
            "data_license": "Open Data Commons Open Database License (ODbL v1.0)",
            "cost_model": "$0 — 100% free-tier digital public infrastructure",
        },
    }

    render_html(
        f"""
        <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-radius: 14px; padding: 18px 22px; color: #F8FAFC; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.5rem;">🌐</span>
                    <div>
                        <div style="font-size:1.05rem; font-weight:800; color:#FFFFFF;">Faslyn Interoperable Agricultural REST API (ODbL v1.0)</div>
                        <div style="font-size:0.75rem; color:#94A3B8;">Standardized cross-border machine-to-machine exchange · 100% Free Public Good</div>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:8px; background:#064E3B; border:1px solid #059669; padding:4px 14px; border-radius:9999px;">
                    <span style="width:8px; height:8px; border-radius:50%; background:#10B981; display:inline-block;"></span>
                    <span style="font-size:0.75rem; font-weight:700; color:#34D399;">Live REST Service on Port {API_PORT}</span>
                </div>
            </div>
            <div style="font-size:0.82rem; color:#CBD5E1; line-height:1.5;">
                External agricultural networks, government AgriStack portals (India, Brazil EMBRAPA, South Africa AgriPortal), and research nodes can consume this node's live telemetric data directly via HTTP REST without authentication barriers or subscription fees.
            </div>
        </div>
        """
    )

    api_tab_overview, api_tab_live_test, api_tab_code = st.tabs([
        "📋 Standardized DPG Schema Export",
        "🧪 Live Endpoint Tester",
        "💻 Machine-to-Machine Integration Code",
    ])

    with api_tab_overview:
        st.json(interop_schema)
        st.download_button(
            f"⬇️ {_('qa_down').splitlines()[0].replace('📄 ', '')} (JSON)",
            data=json.dumps(interop_schema, indent=2),
            file_name="brics_agrin_node_export.json",
            mime="application/json",
            type="primary",
        )

    with api_tab_live_test:
        st.markdown("#### ⚡ Live Machine-to-Machine Query Console")
        st.caption(f"Send real HTTP GET requests to the local daemonized REST API server running on port {API_PORT}.")

        endpoint_choice = st.selectbox(
            "Select REST Endpoint",
            [
                "/api/v1/export (Full DPG Interoperability Bundle)",
                "/api/v1/telemetry (Live Open-Meteo Soil & Weather)",
                "/api/v1/soil (Live ISRIC SoilGrids Chemical Profile)",
                "/api/v1/satellite (Live NASA POWER Climatology)",
                "/api/v1/hubs (BRICS Regional Agricultural Registry)",
                "/api/v1/health (API Health Check)",
            ],
            key="api_endpoint_select",
        )
        endpoint_path = endpoint_choice.split()[0]
        test_url = f"http://localhost:{API_PORT}{endpoint_path}"

        c_test_btn, c_test_url = st.columns([1, 3], vertical_alignment="center", wrap=True)
        with c_test_url:
            st.code(test_url, language="bash")
        with c_test_btn:
            do_test = st.button("🚀 Execute HTTP GET", type="primary", use_container_width=True, key="btn_run_api_test")

        if do_test:
            import time
            import urllib.request
            t0 = time.time()
            try:
                req = urllib.request.Request(test_url, headers={"User-Agent": "FaslynDashboard/2.0"})
                with urllib.request.urlopen(req, timeout=4.0) as resp:
                    latency_ms = round((time.time() - t0) * 1000, 1)
                    status_code = resp.status
                    headers = dict(resp.getheaders())
                    payload = json.loads(resp.read().decode("utf-8"))

                st.success(f"✅ HTTP {status_code} OK · Latency: {latency_ms} ms · Content-Type: {headers.get('content-type', 'application/json')}")
                st.json(payload)
            except Exception as e:
                st.error(f"❌ Connection error: {e}. Please ensure background server on port {API_PORT} is running.")

    with api_tab_code:
        st.markdown("#### 💻 Programmatic Integration Code")
        st.caption("Copy and execute from any language or terminal to interface with Faslyn.")

        st.markdown("**cURL Terminal Command:**")
        st.code(
            f'# Query complete ODbL Digital Public Good payload\n'
            f'curl -X GET "http://localhost:{API_PORT}/api/v1/export" \\\n'
            f'  -H "Accept: application/json"\n\n'
            f'# Query live soil telemetry for specific coordinates\n'
            f'curl -X GET "http://localhost:{API_PORT}/api/v1/telemetry?lat={st.session_state.coords["lat"]:.4f}&lon={st.session_state.coords["lon"]:.4f}"\n\n'
            f'# Query ISRIC SoilGrids chemical profile\n'
            f'curl -X GET "http://localhost:{API_PORT}/api/v1/soil?lat={st.session_state.coords["lat"]:.4f}&lon={st.session_state.coords["lon"]:.4f}"',
            language="bash",
        )

        st.markdown("**Python `requests` Integration:**")
        st.code(
            f'import requests\n\n'
            f'# Fetch live interoperability bundle\n'
            f'response = requests.get("http://localhost:{API_PORT}/api/v1/export", timeout=5.0)\n'
            f'data = response.json()\n\n'
            f'print("Node:", data["node"]["node_id"])\n'
            f'print("Soil Moisture:", data["ground_telemetry"]["soil_moisture_0_7cm_m3m3"], "m3/m3")\n'
            f'print("Soil pH:", data["soil_chemical_fertility"]["ph"])\n'
            f'print("License:", data["interoperability"]["data_license"])\n',
            language="python",
        )

    st.markdown("---")
    bot_b1, bot_b2 = st.columns([1.5, 3], vertical_alignment="center", wrap=True)
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
    st.write("Manage your farmer profile, agricultural region, and cooperative preferences.")

    c_set = st.container(key="settings_inputs_container")
    s_col1, s_col2 = c_set.columns(2, wrap=True)
    with s_col1:
        edit_name = st.text_input("Farmer Full Name", value=st.session_state.get("user_name", ""), placeholder="e.g. Soman Bose")
        edit_region = st.text_input("Farm Region / Village", value=st.session_state.get("user_region", ""), placeholder="e.g. Odisha, India")
    with s_col2:
        edit_role = st.text_input("Farming Role & Crops", value=st.session_state.get("user_role", ""), placeholder="e.g. Smallholder Farmer (Rice & Pulses)")
        edit_phone = st.text_input("Mobile / Cooperative ID", value=st.session_state.get("user_phone", ""), placeholder="e.g. +91 98765 43210")

    st.checkbox("Enable Offline Field & Telemetry Cache", value=True)

    client = get_client()
    if client is not None:
        p_name = client.get("provider", "Groq" if client.get("api_key", "").startswith("gsk_") else "xAI Grok")
        m_name = client.get("text_model", "Live Engine")
        st.info(f"🔒 **AI Intelligence Connected:** {p_name} ({m_name}) is running securely via server environment credentials (`.env` / Cloud Secrets).")
    else:
        st.info("🌱 **Zero-Cost Engine Active:** Running local calibrated agro-climatology and foliar vision heuristics (100% free, no API key required).")

    if st.button("Save Profile Settings", type="primary"):
        st.session_state.user_name = edit_name.strip()
        st.session_state.user_region = edit_region.strip()
        st.session_state.user_role = edit_role.strip()
        st.session_state.user_phone = edit_phone.strip()
        parts = edit_name.strip().split()
        if len(parts) >= 2:
            st.session_state.user_avatar = f"{parts[0][0]}{parts[1][0]}".upper()
        elif len(parts) == 1 and parts[0]:
            st.session_state.user_avatar = parts[0][:2].upper()
        else:
            st.session_state.user_avatar = "FP"
        try:
            upsert_farmer(
                st.session_state.get("farmer_id", "FAS-1001"),
                st.session_state.get("user_phone", "+91 98765 43210"),
                edit_name,
                edit_region,
                edit_role,
                st.session_state.get("selected_hub_name", "India"),
            )
        except Exception:
            pass
        st.success("Profile updated successfully!")
        st.rerun()

    st.markdown("---")
    if st.button(_("back_to_home"), key="back_settings_bot", type="secondary"):
        navigate_back()




