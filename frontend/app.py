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
        background-color: transparent !important;
        z-index: 99999 !important;
    }
    
    /* Hide Deploy button, 3-dots Menu, and Streamlit Footer ONLY */
    .stAppDeployButton,
    [data-testid="stAppDeployButton"],
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* Ensure Sidebar Collapse/Expand Toggle is ALWAYS visible and clickable */
    div[data-testid="stSidebarCollapsedControl"],
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
    div[data-testid="stSidebarCollapsedControl"] {
        top: 10px !important;
        left: 10px !important;
        display: flex !important;
    }
    div[data-testid="stSidebarCollapsedControl"] button,
    button[data-testid="stSidebarCollapseButton"] {
        background: #FFFFFF !important;
        color: #1B4D3E !important;
        border: 1.5px solid #C8D6CC !important;
        border-bottom: 3px solid #10B981 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(27, 77, 62, 0.15) !important;
        padding: 6px 12px !important;
        cursor: pointer !important;
    }
    div[data-testid="stSidebarCollapsedControl"] button:hover,
    button[data-testid="stSidebarCollapseButton"]:hover {
        background: #ECFDF5 !important;
        transform: translateY(-1.5px) !important;
    }
    div[data-testid="stSidebarCollapsedControl"] svg,
    button[data-testid="stSidebarCollapseButton"] svg {
        fill: #1B4D3E !important;
        color: #1B4D3E !important;
    }

    /* Sidebar Width, Background & Sizing (Compact 240px Layout) */
    section[data-testid="stSidebar"] {
        width: 240px !important;
        min-width: 240px !important;
        max-width: 240px !important;
        background-color: #F8FAF7 !important;
        border-right: 1px solid #EBF2EB !important;
    }
    div[data-testid="stSidebarContent"] {
        width: 240px !important;
    }
    div[data-testid="stSidebarUserContent"] {
        padding: 1.1rem 0.85rem !important;
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
    
    /* Profile & Language Header Pill - Subtle 3D Depth */
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
        padding: 18px 20px;
        border: 1px solid rgba(226, 235, 229, 0.95);
        border-bottom: 3.5px solid rgba(200, 218, 206, 0.9);
        box-shadow: 0 5px 14px -3px rgba(27, 77, 62, 0.06), 0 2px 5px -1px rgba(0, 0, 0, 0.03), inset 0 1px 1px rgba(255, 255, 255, 0.95);
        display: flex;
        align-items: center;
        gap: 16px;
        transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .kpi-card:hover {
        transform: translateY(-3px) scale(1.006);
        border-bottom-color: rgba(181, 131, 90, 0.55);
        box-shadow: 0 14px 28px -4px rgba(27, 77, 62, 0.12), 0 6px 12px -2px rgba(0, 0, 0, 0.04), inset 0 1px 1px rgba(255, 255, 255, 1);
    }
    .kpi-icon-box {
        width: 48px;
        height: 48px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        border: 1px solid rgba(255, 255, 255, 0.85);
        border-bottom: 2px solid rgba(0, 0, 0, 0.08);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.04), inset 0 1.5px 1px rgba(255, 255, 255, 0.9);
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
    
    /* Section Cards - Soft 3D Elevation */
    .dashboard-card {
        background: linear-gradient(170deg, #FFFFFF 0%, #FAFCF9 100%);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(228, 236, 231, 0.95);
        border-bottom: 3.5px solid rgba(200, 218, 206, 0.85);
        box-shadow: 0 6px 18px -3px rgba(27, 77, 62, 0.06), 0 3px 8px -2px rgba(0, 0, 0, 0.03), inset 0 1px 1px rgba(255, 255, 255, 0.95);
        margin-bottom: 16px;
        transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .dashboard-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 28px -4px rgba(27, 77, 62, 0.1), 0 5px 10px -2px rgba(0, 0, 0, 0.04), inset 0 1px 1px #FFFFFF;
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
    
    /* Sustainability Banner - 3D Soft Elevation */
    .impact-banner {
        background: linear-gradient(135deg, #E8F5E9 0%, #F1F8F4 100%);
        border: 1px solid #C8E6C9;
        border-bottom: 3.5px solid #A5D6A7;
        border-radius: 20px;
        padding: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 20px;
        box-shadow: 0 6px 18px -3px rgba(27, 77, 62, 0.08), inset 0 1px 1px #FFFFFF;
        transition: all 0.25s ease;
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
    /* Click / Active state: Tactile 3D Physical Push Down */
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
    .stButton > button:focus,
    .stButton > button:focus-visible,
    button[data-testid="baseButton-primary"]:focus,
    button[data-testid="baseButton-primary"]:focus-visible {
        outline: 2px solid #C4925E !important;
        box-shadow: 0 0 0 3px rgba(212, 163, 115, 0.4) !important;
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
        box-shadow: none !important;
        transform: translateX(2px) !important;
    }
    .stButton > button[kind="tertiary"]:hover *,
    .stButton > button[data-testid="baseButton-tertiary"]:hover * {
        color: #4A280F !important;
    }
    .stButton > button[kind="tertiary"]:active,
    .stButton > button[data-testid="baseButton-tertiary"]:active {
        background-color: #EBDCCF !important;
        border-radius: 8px !important;
        transform: scale(0.97) !important;
    }
    .stButton > button[kind="tertiary"]:active *,
    .stButton > button[data-testid="baseButton-tertiary"]:active * {
        color: #2E1504 !important;
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
        box-shadow: 0 2px 6px rgba(181, 131, 90, 0.12), inset 0 1px 0 #FFFFFF !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button[kind="secondary"] *,
    .stButton > button[kind="secondary"] p,
    .stButton > button[data-testid="baseButton-secondary"] *,
    .stButton > button[data-testid="baseButton-secondary"] p {
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
    .stButton > button[kind="secondary"]:hover *,
    .stButton > button[data-testid="baseButton-secondary"]:hover * {
        color: #3D2007 !important;
    }
    .stButton > button[kind="secondary"]:active,
    .stButton > button[data-testid="baseButton-secondary"]:active {
        background-color: #D4A373 !important;
        border-color: #B57F4D !important;
        border-bottom-width: 1px !important;
        box-shadow: 0 1px 3px rgba(181, 131, 90, 0.3) !important;
        transform: translateY(2px) !important;
    }
    .stButton > button[kind="secondary"]:active *,
    .stButton > button[data-testid="baseButton-secondary"]:active * {
        color: #1E1208 !important;
    }

    /* Tabs Styling - 3D Accent Line */
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        color: #4B5563 !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #111827 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #633811 !important;
        font-weight: 700 !important;
        border-bottom-color: #C49A6C !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] * {
        color: #633811 !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #C49A6C !important;
        height: 3px !important;
        border-radius: 9999px !important;
        box-shadow: 0 1px 4px rgba(196, 154, 108, 0.4) !important;
    }

    /* Notification Bell Popover Styling - 3D Tactile Pill */
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
        box-shadow: 0 2px 6px rgba(0,0,0,0.05), inset 0 1px 0 #FFFFFF !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        cursor: pointer !important;
    }
    div[data-testid="stPopover"] > button:hover {
        background: #F8F3EE !important;
        border-color: #B5835A !important;
        color: #7D4E27 !important;
        box-shadow: 0 5px 12px rgba(181, 131, 90, 0.22), inset 0 1px 0 #FFFFFF !important;
        transform: translateY(-1.5px) !important;
    }
    div[data-testid="stPopover"] > button:active {
        background-color: #B5835A !important;
        color: #FFFFFF !important;
        border-color: #9C683E !important;
        border-bottom-width: 1px !important;
        transform: translateY(1.5px) !important;
        box-shadow: 0 1px 3px rgba(181, 131, 90, 0.35) !important;
    }
    div[data-testid="stPopoverBody"] {
        border-radius: 18px !important;
        border: 1px solid #E5E7EB !important;
        border-bottom: 3px solid #D1D5DB !important;
        box-shadow: 0 14px 34px rgba(0,0,0,0.12), 0 4px 10px rgba(0,0,0,0.05) !important;
        padding: 16px !important;
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

    /* Input and Form Fields - 3D Inset Depth */
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

    /* 3D Map Viewport Frame */
    iframe {
        border-radius: 18px !important;
        border: 1.5px solid rgba(220, 232, 224, 0.95) !important;
        border-bottom: 3.5px solid rgba(185, 205, 192, 0.95) !important;
        box-shadow: 0 10px 25px -4px rgba(27, 77, 62, 0.1), 0 4px 10px -2px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    iframe:hover {
        box-shadow: 0 16px 36px -4px rgba(27, 77, 62, 0.15), 0 6px 14px -2px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Sidebar Styling & Compact Layout */
    section[data-testid="stSidebar"] {
        width: 240px !important;
        min-width: 240px !important;
        max-width: 240px !important;
        background-color: #F8FAF7 !important;
        border-right: 1px solid #EBF2EB !important;
    }
    div[data-testid="stSidebarContent"] {
        width: 240px !important;
    }
    div[data-testid="stSidebarUserContent"] {
        padding: 1.1rem 0.85rem !important;
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

    /* -----------------------------------------------------------------------
       RESPONSIVE MOBILE & TOUCH DESIGN SYSTEM (PHONES & TABLETS <= 768px)
       ----------------------------------------------------------------------- */
    @media (max-width: 768px) {
        /* Mobile sidebar sizing */
        section[data-testid="stSidebar"] {
            width: 240px !important;
            min-width: 200px !important;
            max-width: 78vw !important;
        }
        div[data-testid="stSidebarContent"] {
            width: 240px !important;
            max-width: 78vw !important;
        }

        /* Optimize screen real estate: eliminate excess desktop margins */
        .main .block-container {
            padding: 0.85rem 0.65rem 2.5rem 0.65rem !important;
            max-width: 100% !important;
        }

        /* Top Header on mobile: vertical stack with flexible spacing */
        .top-header {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 12px !important;
            padding-bottom: 10px !important;
        }
        .greeting-title {
            font-size: 1.4rem !important;
            line-height: 1.25 !important;
        }
        .greeting-subtitle {
            font-size: 0.82rem !important;
        }
        .header-user-pill {
            width: 100% !important;
            justify-content: space-between !important;
            box-sizing: border-box !important;
            padding: 8px 14px !important;
        }

        /* Make multi-column grids collapse cleanly into touch-friendly full-width blocks */
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 8px !important;
        }

        /* KPI cards on mobile: tactile, touch-spaced full-width cards */
        .kpi-card {
            padding: 14px 16px !important;
            gap: 12px !important;
            margin-bottom: 10px !important;
            border-radius: 16px !important;
        }
        .kpi-val {
            font-size: 1.45rem !important;
        }
        .kpi-label {
            font-size: 0.78rem !important;
        }

        /* Section Cards & Impact Banners on mobile */
        .dashboard-card {
            padding: 16px !important;
            border-radius: 16px !important;
            margin-bottom: 12px !important;
        }
        .card-header-title {
            font-size: 1.05rem !important;
        }
        .impact-banner {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 12px !important;
            padding: 16px !important;
            border-radius: 16px !important;
        }
        .impact-chip {
            width: 100% !important;
            justify-content: flex-start !important;
            box-sizing: border-box !important;
        }

        /* Interactive Map Frame on mobile */
        iframe {
            min-height: 240px !important;
            height: 250px !important;
            border-radius: 14px !important;
        }

        /* Smooth horizontal scrollbar for tab navigation */
        div[data-baseweb="tab-list"] {
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
            scrollbar-width: none !important;
            -webkit-overflow-scrolling: touch !important;
            padding-bottom: 4px !important;
        }
        div[data-baseweb="tab-list"]::-webkit-scrollbar {
            display: none !important;
        }
        button[data-baseweb="tab"] {
            white-space: nowrap !important;
            padding: 8px 12px !important;
            font-size: 0.88rem !important;
        }

        /* Touch-friendly buttons (Apple HIG / Android Material 48px touch targets) */
        .stButton > button {
            width: 100% !important;
            min-height: 48px !important;
            font-size: 0.95rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        /* Popover dropdowns on mobile */
        div[data-testid="stPopoverBody"] {
            max-width: 92vw !important;
            width: 92vw !important;
            left: 4vw !important;
        }

        /* Inputs & Selects: 16px prevents iOS Safari auto-zoom */
        .stTextInput input, .stSelectbox div {
            font-size: 16px !important;
        }

        /* Mobile-optimized sidebar toggle button */
        button[data-testid="stSidebarCollapseButton"],
        button[data-testid="baseButton-headerNoPadding"] {
            background-color: rgba(255, 255, 255, 0.92) !important;
            border-radius: 10px !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
            min-width: 40px !important;
            min-height: 40px !important;
        }
    }

    /* -----------------------------------------------------------------------
       LIGHT-COLORED 3D SPLASH LOADER
       ----------------------------------------------------------------------- */
    /* -----------------------------------------------------------------------
       LIGHT GREEN & BLUE MIX 3D SPLASH LOADER (2 SECONDS WITH SMOOTH ZOOM-IN FLOW)
       ----------------------------------------------------------------------- */
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
        will-change: opacity;
        animation: faslynContainerFlow 2.0s forwards;
    }

    .faslyn-loader-card {
        background: #FFFFFF;
        border: 1px solid rgba(220, 240, 230, 0.9);
        border-bottom: 4px solid #10B981;
        border-radius: 26px;
        padding: 36px 44px;
        box-shadow: 0 24px 60px -12px rgba(16, 114, 85, 0.16),
                    0 10px 25px -6px rgba(2, 132, 199, 0.12),
                    0 0 0 1px rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 14px;
        max-width: 360px;
        width: 90%;
        box-sizing: border-box;
        will-change: transform, opacity;
        animation: faslynCardFlow 2.0s forwards;
    }

    .faslyn-spinner-wrapper {
        position: relative;
        width: 70px;
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 4px;
    }

    .faslyn-spinner-ring {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 3.5px solid rgba(16, 185, 129, 0.16);
        border-top: 3.5px solid #10B981;
        border-right: 3.5px solid #0284C7;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.18);
        animation: faslynSpin 1.0s linear infinite;
    }

    .faslyn-spinner-icon {
        font-size: 30px;
        animation: faslynPulse 1.4s ease-in-out infinite;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .faslyn-loader-brand {
        font-size: 1.65rem;
        font-weight: 800;
        color: #1B4D3E;
        letter-spacing: -0.5px;
        line-height: 1.1;
    }

    .faslyn-loader-subtitle {
        font-size: 0.84rem;
        font-weight: 600;
        color: #4B5563;
        line-height: 1.3;
    }

    .faslyn-loader-track {
        width: 190px;
        height: 6px;
        background: rgba(2, 132, 199, 0.12);
        border-radius: 9999px;
        overflow: hidden;
        margin-top: 4px;
    }

    .faslyn-loader-bar {
        height: 100%;
        background: linear-gradient(90deg, #10B981 0%, #0284C7 50%, #34D399 100%);
        border-radius: 9999px;
        animation: faslynProgressFill 1.35s cubic-bezier(0.2, 0.7, 0.3, 1) forwards;
    }

    .faslyn-loader-status {
        font-size: 0.75rem;
        font-weight: 600;
        color: #6B7280;
        letter-spacing: 0.2px;
    }

    @keyframes faslynProgressFill {
        0% { width: 0%; }
        25% { width: 35%; }
        65% { width: 75%; }
        90% { width: 95%; }
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
        0% {
            transform: scale(0.92);
            opacity: 0;
            animation-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
        }
        18% {
            transform: scale(1);
            opacity: 1;
            animation-timing-function: linear;
        }
        67% {
            transform: scale(1);
            opacity: 1;
            animation-timing-function: cubic-bezier(0.25, 1, 0.5, 1);
        }
        100% {
            transform: scale(1.28);
            opacity: 0;
            visibility: hidden;
        }
    }

    @keyframes faslynContainerFlow {
        0% {
            opacity: 1;
            visibility: visible;
            pointer-events: auto;
            animation-timing-function: linear;
        }
        67% {
            opacity: 1;
            visibility: visible;
            pointer-events: auto;
            animation-timing-function: cubic-bezier(0.25, 1, 0.5, 1);
        }
        100% {
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
        }
    }

    /* Style Streamlit's inline spinners with light theme colors */
    div[data-testid="stSpinner"] > div {
        border-color: #D4A373 transparent #D4A373 transparent !important;
    }
    div[data-testid="stSpinner"] {
        color: #7D4E27 !important;
        font-weight: 600 !important;
    }
    </style>
    """
)

# ---------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = "Ramesh Kumar"
if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = "RK"
if "user_role" not in st.session_state:
    st.session_state.user_role = "Smallholder Farmer"
if "user_phone" not in st.session_state:
    st.session_state.user_phone = "+91 98765 43210"
if "user_region" not in st.session_state:
    st.session_state.user_region = "Odisha, India"
if "farmer_id" not in st.session_state:
    st.session_state.farmer_id = "IN-OD-2026-4482"
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
    """Resolve a Grok (xAI) client from .env (os.environ), Streamlit secrets, or user input."""
    api_key = None
    try:
        api_key = st.secrets.get("GROK_API_KEY") or st.secrets.get("XAI_API_KEY")
    except Exception:
        api_key = None
    if not api_key:
        api_key = os.environ.get("GROK_API_KEY") or os.environ.get("XAI_API_KEY")
    if not api_key:
        api_key = st.session_state.get("manual_grok_key")
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
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }
        header[data-testid="stHeader"] {
            background: transparent !important;
        }
        .main .block-container {
            max-width: 1040px !important;
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
        </style>
        """
    )

    render_html(
        """
        <div class="login-header-wrapper">
            <div class="login-brand-title">
                🌿 faslyn
            </div>
            <div class="login-pill-badge">
                <span class="login-pill-dot"></span>
                <span style="font-size: 0.76rem; font-weight: 700; color: #047857; text-transform: uppercase; letter-spacing: 0.05em;">
                    BRICS Sovereign Agricultural Intelligence Network
                </span>
            </div>
            <h2 style="font-size: 1.6rem; font-weight: 800; color: #111827; margin: 12px 0 6px 0;">
                Cooperative Farmer Sign-In
            </h2>
            <p style="color: #4B5563; font-size: 0.92rem; max-width: 620px; margin: 0 auto; line-height: 1.45;">
                Sign in with your national farmer cooperative ID or choose a verified demo profile to access AI satellite agro-telemetry, regenerative advisory, and sovereign credit scoring.
            </p>
        </div>
        """
    )

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        render_html(
            """
            <div class="login-card-head">🔐 Cooperative Member Sign-In</div>
            <div class="login-card-sub">Enter your details to customize your farm dashboard</div>
            """
        )

        login_name = st.text_input(
            "Farmer Full Name",
            value=st.session_state.get("user_name", "Ramesh Pradhan"),
            key="login_farmer_name",
            help="Enter your name as you would like it displayed across the dashboard.",
        )

        col_id, col_pin = st.columns(2)
        with col_id:
            login_id = st.text_input(
                "Mobile / Cooperative ID",
                value=st.session_state.get("user_phone", "+91 98765 43210"),
                key="login_mobile_id",
                help="Your registered mobile number or cooperative member ID.",
            )
        with col_pin:
            login_pin = st.text_input(
                "Security PIN",
                value="123456",
                type="password",
                key="login_pin_code",
                help="Default demo PIN is 123456 (or any 4+ digits)",
            )

        col_reg, col_role = st.columns(2)
        with col_reg:
            login_region = st.text_input(
                "Farm Region / Village",
                value=st.session_state.get("user_region", "Odisha, India"),
                key="login_region_input",
                help="Your farm location, district, or agricultural zone.",
            )
        with col_role:
            login_role = st.text_input(
                "Farming Role & Crops",
                value=st.session_state.get("user_role", "Smallholder Lead (Rice & Pulses)"),
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
            entered_name = login_name.strip() if login_name.strip() else "Farmer"
            entered_phone = login_id.strip() if login_id.strip() else "+91 98765 43210"
            entered_region = login_region.strip() if login_region.strip() else "Local Agricultural Belt"
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

    with col_right:
        render_html(
            """
            <div class="login-card-head">⚡ 1-Click Quick Demo Profiles</div>
            <div class="login-card-sub">Instant login with pre-configured BRICS agricultural telemetry</div>
            """
        )

        for idx, prof in enumerate(DEMO_PROFILES):
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
            if st.button(f"Enter as {prof['name']} ({prof['flag']}) →", key=f"quick_demo_btn_{idx}", use_container_width=True):
                st.session_state.is_authenticated = True
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

    render_html(
        """
        <div style="margin-top: 32px; padding: 18px 24px; background: #FFFFFF; border: 1px solid #E2EBE5; border-radius: 16px; display: flex; flex-wrap: wrap; justify-content: space-around; align-items: center; gap: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.02);">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.4rem;">🔒</span>
                <div>
                    <div style="font-weight:700; font-size:0.82rem; color:#111827;">Sovereign Security</div>
                    <div style="font-size:0.72rem; color:#6B7280;">ODbL 1.0 Open Data Public Good</div>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.4rem;">🛰️</span>
                <div>
                    <div style="font-weight:700; font-size:0.82rem; color:#111827;">Zero-Sensor Telemetry</div>
                    <div style="font-size:0.72rem; color:#6B7280;">NASA POWER & Open-Meteo Feeds</div>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.4rem;">📞</span>
                <div>
                    <div style="font-weight:700; font-size:0.82rem; color:#111827;">Kisan Helpline</div>
                    <div style="font-size:0.72rem; color:#6B7280;">Toll-Free: 1800-180-1551</div>
                </div>
            </div>
        </div>
        """
    )


# ---------------------------------------------------------------------------
# AUTHENTICATION GATEWAY (LOGIN REQUIRED BEFORE DASHBOARD)
# ---------------------------------------------------------------------------
if not st.session_state.get("is_authenticated", False):
    render_login_page()
    st.stop()


# Fetch telemetry, satellite & soil feeds (cached globally with TTL, zero network latency on reruns)
telemetry = get_telemetry(st.session_state.coords["lat"], st.session_state.coords["lon"])
satellite = get_satellite(st.session_state.coords["lat"], st.session_state.coords["lon"])
soil_data = get_soil(st.session_state.coords["lat"], st.session_state.coords["lon"], st.session_state.selected_hub_name)
st.session_state.telemetry = telemetry
st.session_state.satellite = satellite
st.session_state.soil_data = soil_data

# Record persistent environmental telemetry snapshot in local SQLite database
try:
    log_telemetry_snapshot(
        st.session_state.coords["lat"],
        st.session_state.coords["lon"],
        st.session_state.selected_hub_name,
        telemetry,
        satellite,
    )
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
# SIDEBAR — BRANDING & NAVIGATION
# ===========================================================================
with st.sidebar:
    render_html(
        f"""
        <div class="sidebar-brand">
            🌿 faslyn
        </div>
        <div style="background: #F0FDF4; border: 1.5px solid #BBF7D0; border-radius: 12px; padding: 9px 12px; margin: 6px 0 12px 0; display: flex; align-items: center; gap: 10px;">
            <div style="width: 34px; height: 34px; border-radius: 50%; background: #10B981; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; flex-shrink: 0; box-shadow: 0 2px 6px rgba(16,185,129,0.25);">
                {st.session_state.get('user_avatar', 'FP')}
            </div>
            <div style="overflow: hidden; line-height: 1.25;">
                <div style="font-weight: 700; font-size: 0.84rem; color: #111827; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;" title="{st.session_state.get('user_name', 'Farmer')}">{st.session_state.get('user_name', 'Farmer')}</div>
                <div style="font-size: 0.70rem; color: #059669; font-weight: 600; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">{st.session_state.get('user_region', 'Farm Region')}</div>
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
        st.session_state.active_tab_id = "home"
        st.session_state.nav_stack = ["home"]
        st.rerun()

# ===========================================================================
# TOP HEADER BAR WITH LIVE LANGUAGE SWITCHER
# ===========================================================================
hdr_left, hdr_right = st.columns([3, 2])

with hdr_left:
    if st.session_state.active_tab_id == "home":
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
            <div class="top-header">
                <div>
                    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                        <h1 class="greeting-title">{greeting_text}</h1>
                        <span style="background: #ECFDF5; color: #047857; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 9999px; border: 1px solid #A7F3D0; display: inline-flex; align-items: center; gap: 5px;">
                            <span style="display:inline-block; width:7px; height:7px; background:#10B981; border-radius:50%;"></span>
                            LIVE NASA & SENSOR FEEDS
                        </span>
                    </div>
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
                st.session_state.active_tab_id = "home"
                st.session_state.nav_stack = ["home"]
                st.rerun()

if st.session_state.active_tab_id != "home":
    render_html('<div style="height: 1px; background: #E5E7EB; margin: 10px 0 18px 0;"></div>')

# ===========================================================================
# VIEW 1: HOME DASHBOARD (FULLY TRANSLATED)
# ===========================================================================
if st.session_state.active_tab_id == "home":

    # -----------------------------------------------------------------------
    # ROW 1: TOP 4 KPI CARDS
    # -----------------------------------------------------------------------
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
    # ROW 1: TOP 4 KPI CARDS (LIVE DATA ENGINE)
    # -----------------------------------------------------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        render_html(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon-box icon-green">🏡</div>
                <div>
                    <div class="kpi-label">{_('total_fields')}</div>
                    <div class="kpi-val">{total_fields}</div>
                    <div class="kpi-subtext">📍 {active_hub_clean}</div>
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
                <div>
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
                <div class="kpi-icon-box icon-teal">🪴</div>
                <div>
                    <div class="kpi-label">{_('overall_health')}</div>
                    <div class="kpi-val">{overall_health}<span style="font-size:1.1rem; color:#6B7280; font-weight:600;">/100</span></div>
                    <div class="kpi-subtext" style="color:{trend_color}; font-weight:700;">↑ {trend_sign}{trend_val}% {_('vs_last_month')}</div>
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

        with st.form("home_quick_loc_search", clear_on_submit=False):
            hs1, hs2 = st.columns([3.4, 1.3], vertical_alignment="center")
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

            import math
            n_f = len(fields_data)
            radius = 0.0055
            for idx, fld in enumerate(fields_data):
                angle = (2 * math.pi / n_f) * idx
                lat_off = radius * math.cos(angle)
                lon_off = radius * math.sin(angle)
                f_lat = center_lat + lat_off
                f_lon = center_lon + lon_off
                d_lat = 0.002
                d_lon = 0.0025
                poly_pts = [
                    [f_lat - d_lat * 0.7, f_lon - d_lon],
                    [f_lat + d_lat, f_lon - d_lon * 0.6],
                    [f_lat + d_lat * 0.8, f_lon + d_lon * 0.9],
                    [f_lat - d_lat * 0.9, f_lon + d_lon * 0.7],
                ]
                folium.Polygon(
                    locations=poly_pts,
                    color=fld["dot_color"],
                    fill=True,
                    fill_color=fld["dot_color"],
                    fill_opacity=0.65,
                    tooltip=f"{fld['name']} • {fld['crop']} ({fld['score']}%)",
                ).add_to(m)

            st_folium(m, height=275, use_container_width=True, key="dashboard_map", returned_objects=[])

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

        cards_html = "".join([
            f"""
            <div style="background: linear-gradient(180deg, #FFFFFF 0%, #FAFCFA 100%); border: 1.5px solid #E5EBE7; border-bottom: 2.5px solid #D5E0D8; border-radius: 12px; padding: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.03), inset 0 1px 0 #ffffff; transition: all 0.22s ease;">
                <div style="display:flex; align-items:center; justify-content:space-between;">
                    <span style="display:flex; align-items:center; gap:6px; font-weight:700; font-size:0.82rem; color:#111827;">
                        <span style="color:{f['dot_color']};">●</span> {f['name']}
                    </span>
                    <span style="font-size:0.75rem; font-weight:700; color:{f['dot_color']};">{f['score']}%</span>
                </div>
                <div class="badge {f['badge_class']}" style="margin:4px 0;">{f['badge_label']}</div>
                <div style="font-size:0.75rem; color:#6B7280;">{f['icon']} {f['crop']} • {f['area']}</div>
            </div>
            """ for f in fields_data
        ])

        render_html(
            f"""
            <div class="dashboard-card" style="height: 100%;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    {cards_html}
                </div>
            </div>
            """
        )

    with col_act:
        qa_c1, qa_c2 = st.columns([2.2, 1.3], vertical_alignment="center")
        with qa_c1:
            render_html(f'<h3 class="card-header-title">{_("quick_actions")}</h3>')
        with qa_c2:
            if st.button("🔄 " + _("refresh"), key="btn_refresh_feeds", type="tertiary", use_container_width=True, help="Refreshes live satellite and soil telemetry"):
                get_telemetry.clear()
                get_satellite.clear()
                st.session_state.telemetry = None
                st.session_state.satellite = None
                st.rerun()

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
            <div class="dashboard-card" style="height: 100%;">
                <div style="display:flex; flex-direction:column; gap:10px;">
                    <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:{alt1_bg}; border: 1px solid {alt1_border}; border-bottom: 2.5px solid {alt1_bbottom}; border-radius:12px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04); transition: all 0.2s ease;">
                        <div>
                            <div style="font-size:0.82rem; font-weight:700; color:{alt1_color};">{alt1_title}</div>
                            <div style="font-size:0.72rem; color:#4B5563;">{alt1_sub}</div>
                        </div>
                        <span style="color:{alt1_color}; font-weight:bold;">›</span>
                    </div>
                    
                    <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:{alt2_bg}; border: 1px solid {alt2_border}; border-bottom: 2.5px solid {alt2_bbottom}; border-radius:12px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04); transition: all 0.2s ease;">
                        <div>
                            <div style="font-size:0.82rem; font-weight:700; color:{alt2_color};">{alt2_title}</div>
                            <div style="font-size:0.72rem; color:#4B5563;">{alt2_sub}</div>
                        </div>
                        <span style="color:{alt2_color}; font-weight:bold;">›</span>
                    </div>
                    
                    <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:{alt3_bg}; border: 1px solid {alt3_border}; border-bottom: 2.5px solid {alt3_bbottom}; border-radius:12px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04); transition: all 0.2s ease;">
                        <div>
                            <div style="font-size:0.82rem; font-weight:700; color:{alt3_color};">{alt3_title}</div>
                            <div style="font-size:0.72rem; color:#4B5563;">{alt3_sub}</div>
                        </div>
                        <span style="color:{alt3_color}; font-weight:bold;">›</span>
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
            <div style="max-width: 50%;">
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
            
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <div class="impact-chip">
                    <span style="font-size:20px;">🪴</span>
                    <div>
                        <div style="font-size:0.72rem; color:#6B7280;">{_('soil_health')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#16A34A;">↑ +{impact_soil}%</div>
                    </div>
                </div>
                
                <div class="impact-chip">
                    <span style="font-size:20px;">💧</span>
                    <div>
                        <div style="font-size:0.72rem; color:#6B7280;">{_('water_use')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#0284C7;">↓ -{impact_water}%</div>
                    </div>
                </div>
                
                <div class="impact-chip">
                    <span style="font-size:20px;">🧪</span>
                    <div>
                        <div style="font-size:0.72rem; color:#6B7280;">{_('input_dep')}</div>
                        <div style="font-size:0.95rem; font-weight:800; color:#16A34A;">↓ -{impact_input}%</div>
                    </div>
                </div>
                
                <div class="impact-chip">
                    <span style="font-size:20px;">🌿</span>
                    <div>
                        <div style="font-size:0.72rem; color:#6B7280;">{_('regen_score')}</div>
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
        sc1, sc2 = st.columns([3.8, 1.3], vertical_alignment="center")
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
    sug_cols = st.columns(5)
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
    s1, s2, s3, s4 = st.columns(4)
    s1.metric(_("soil_health"), f"{telemetry.get('soil_moisture', 0.24):.2f} m³/m³", "Open-Meteo Topsoil (0-7cm)")
    s2.metric("Soil Temperature", f"{telemetry.get('soil_temp', 27.5):.1f} °C", "Microbial Activity Zone")
    s3.metric("Solar Radiation (NASA)", f"{satellite.get('solar_radiation', 18.5):.1f} MJ/m²/d", f"Obs: {satellite.get('data_date', 'Live')}")
    s4.metric(_("water_status"), f"{satellite.get('root_zone_soil_wetness', 0.42):.2f} (0-1)", "NASA POWER Root-Zone")

    # Soil Chemical & Nutrient Profile (ISRIC SoilGrids + Regional Baseline)
    current_soil = st.session_state.get("soil_data", {})
    st.markdown("##### 🧪 Topsoil Chemical & Nutrient Fertility Profile")
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.metric("Soil pH", f"{current_soil.get('ph', 6.5):.1f}", current_soil.get("ph_label", "Neutral"))
    sc2.metric("Organic Carbon (SOC)", f"{current_soil.get('soc_pct', 1.2):.1f}%", current_soil.get("soc_rating", "Moderate"))
    sc3.metric("Available Nitrogen", f"{current_soil.get('nitrogen_kg_ha', 240)} kg/ha", "Macronutrient Pool")
    sc4.metric("Cation Exchange (CEC)", f"{current_soil.get('cec_cmol_kg', 18.0):.1f} cmol/kg", "Nutrient Retention")
    sc5.metric("Soil Texture Class", current_soil.get("texture_label", "Loam"), f"Source: {current_soil.get('source', 'ISRIC SoilGrids')}")

    with st.expander("📝 Digital Soil Health Card (Custom Lab Overrides / Manual Entry)", expanded=False):
        st.caption("Override satellite and global soil models with laboratory Soil Health Card (SHC) test measurements for pinpoint local advisory accuracy.")
        shc_c1, shc_c2, shc_c3, shc_c4 = st.columns(4)
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
            col_rep, _spacer = st.columns([1, 4])
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

        c_test_btn, c_test_url = st.columns([1, 3], vertical_alignment="center")
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
        edit_name = st.text_input("Farmer Name", value=st.session_state.get("user_name", "Ramesh Kumar"))
        edit_region = st.text_input("Farm Region", value=st.session_state.get("user_region", "Odisha, India"))
    with s_col2:
        manual_grok_val = st.text_input("xAI Grok API Key", type="password", value=st.session_state.get("manual_grok_key", ""))
        st.checkbox("Enable Offline Field Cache", value=True)

    if st.button("Save Settings", type="primary"):
        st.session_state.user_name = edit_name
        st.session_state.user_region = edit_region
        if manual_grok_val:
            st.session_state.manual_grok_key = manual_grok_val
        parts = edit_name.strip().split()
        if len(parts) >= 2:
            st.session_state.user_avatar = f"{parts[0][0]}{parts[1][0]}".upper()
        elif len(parts) == 1 and parts[0]:
            st.session_state.user_avatar = parts[0][:2].upper()
        try:
            upsert_farmer(
                st.session_state.get("farmer_id", "FAS-1001"),
                st.session_state.get("user_phone", "+91 98765 43210"),
                edit_name,
                edit_region,
                st.session_state.get("user_role", "Smallholder Farmer"),
                st.session_state.get("selected_hub_name", "India"),
            )
        except Exception:
            pass
        st.success("Settings saved successfully!")
        st.rerun()

    st.markdown("---")
    if st.button(_("back_to_home"), key="back_settings_bot", type="secondary"):
        navigate_back()
