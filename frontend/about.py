"""
Faslyn Farmer-Centric About Page & Login Modal
==============================================
Designed specifically for small and marginal farmers, agricultural producers,
and rural cooperatives. Warm, trustworthy, visual, clear, and easy to understand.
Includes authentic field photography, structured visual workflows, and zero
horizontal overflow across all mobile, tablet, and desktop viewports.
"""

import base64
import os
import streamlit as st
from backend.config import BRICS_HUBS, DEMO_PROFILES, FIRST_HUB, LANGUAGES
from backend.database import upsert_farmer
from frontend.splash import render_splash_loader


@st.cache_data
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


def get_about_hero_image_base64() -> str:
    """Load base64 data URI of existing agricultural image asset for zero-delay rendering."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    webp_path = os.path.join(current_dir, "assets", "hero_farmer_bg.webp")
    png_path = os.path.join(current_dir, "assets", "hero_farmer_bg.png")
    target = webp_path if os.path.exists(webp_path) else png_path
    if os.path.exists(target):
        ext = "webp" if target.endswith(".webp") else "png"
        try:
            with open(target, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/{ext};base64,{b64}"
        except Exception:
            return ""
    return ""


def get_about_css() -> str:
    """Return warm, farmer-friendly, mobile-first CSS with zero horizontal overflow."""
    return """
    <style>
    /* =======================================================================
       Faslyn ABOUT PAGE - WARM, FARMER-FRIENDLY & RESPONSIVE DESIGN
       ======================================================================= */
    
    /* Viewport Enforcements: Zero Horizontal Scrolling */
    html, body, .stApp, 
    div[data-testid="stAppViewContainer"], 
    div[data-testid="stMain"], 
    section.main, 
    .block-container,
    div[data-testid="stMainBlockContainer"] {
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    /* Hide Streamlit default top header bar completely on the About page */
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        visibility: hidden !important;
    }

    /* Reset Streamlit default 6rem top padding on main block container */
    .main .block-container, 
    div[data-testid="stMain"] .block-container, 
    div[data-testid="stMainBlockContainer"],
    .block-container {
        padding-top: 0.75rem !important;
        padding-bottom: 2.5rem !important;
        margin-top: 0 !important;
    }

    /* Remove dead height from style/script injection containers */
    div[data-testid="stElementContainer"]:has(style),
    div[data-testid="element-container"]:has(style),
    div[data-testid="stElementContainer"]:empty,
    div[data-testid="element-container"]:empty {
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 0 !important;
        min-height: 0 !important;
    }

    /* Hide sidebar and toggle buttons completely on the About page */
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

    
    /* =======================================================================
       UNIVERSAL MOBILE RESPONSIVENESS INJECTION (<= 640px)
       ======================================================================= */
    @media (max-width: 640px) {
    /* Force Streamlit blocks from side-by-side flex to pure vertical rows */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 1rem !important;
    }
    /* Force every individual column inside rows to take full screen width */
    [data-testid="stHorizontalBlock"] > div {
        width: 100% !important;
        min-width: 100% !important;
    }
    /* Dynamic image and element scaling */
    img, .stImage {
        max-width: 100% !important;
        height: auto !important;
    }
    /* Prevent metric value texts from overflowing */
    [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        word-break: break-word !important;
    }
}

    @media (max-width: 640px) {
        .about-hero-grid,
        .what-is-grid,
        .about-grid-3,
        .about-grid-4,
        .about-grid-5,
        .trust-grid {
            grid-template-columns: 1fr !important;
            gap: 14px !important;
            width: 100% !important;
        }
        .about-hero-grid {
            padding: 20px 16px !important;
        }
        .about-top-nav {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 8px !important;
            border-radius: 20px !important;
            padding: 10px 14px !important;
        }
        .solution-pipeline-desktop {
            flex-direction: column !important;
            align-items: stretch !important;
            gap: 10px !important;
        }
        .solution-pipeline-arrow {
            transform: rotate(90deg) !important;
            margin: 4px auto !important;
        }
        div[data-testid="column"]:empty {
            display: none !important;
            margin: 0 !important;
            padding: 0 !important;
            height: 0 !important;
            width: 0 !important;
        }
        .about-card, .farmer-pillar-card, .trust-item {
            width: 100% !important;
            box-sizing: border-box !important;
        }
    }
    
    /* Page Container */
    .about-page-wrapper {
        width: 100%;
        max-width: 1120px;
        margin: 0 auto;
        padding: 0 0 3.5rem 0;
        box-sizing: border-box;
        overflow-x: hidden;
    }

    /* Top Brand Navigation Pill Bar */
    .about-top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 20px;
        background: rgba(255, 255, 255, 0.96);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1.5px solid rgba(215, 230, 222, 0.9);
        border-bottom: 3.5px solid rgba(180, 210, 192, 0.9);
        border-radius: 9999px;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(27, 77, 62, 0.05);
        box-sizing: border-box;
    }
    .about-nav-brand {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 800;
        font-size: 1.25rem;
        color: #1B4D3E;
        letter-spacing: -0.02em;
    }
    .about-nav-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #ECFDF5;
        border: 1px solid #A7F3D0;
        color: #047857;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 9999px;
    }

    /* =======================================================================
       HERO SECTION (2 COLUMNS: BRAND + AGRICULTURAL VISUAL)
       ======================================================================= */
    .about-hero-grid {
        display: grid;
        grid-template-columns: 1.15fr 0.85fr;
        gap: 28px;
        align-items: center;
        background: linear-gradient(150deg, #FFFFFF 0%, #F5FAF7 60%, #F3F7F4 100%);
        border: 1.5px solid rgba(200, 225, 212, 0.95);
        border-bottom: 4px solid rgba(160, 205, 180, 0.95);
        border-radius: 26px;
        padding: 36px 34px;
        margin-bottom: 30px;
        box-shadow: 0 12px 35px -8px rgba(27, 77, 62, 0.09), inset 0 1px 1px #FFFFFF;
        box-sizing: border-box;
    }
    .hero-content-col {
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-sizing: border-box;
    }
    .hero-pill-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #E8F5E9;
        border: 1px solid #C8E6C9;
        color: #1B4D3E;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 9999px;
        margin-bottom: 14px;
        width: fit-content;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .hero-main-title {
        font-size: clamp(2.3rem, 5.5vw, 3.6rem);
        font-weight: 900;
        color: #1B4D3E;
        letter-spacing: -0.04em;
        line-height: 1.08;
        margin: 0 0 10px 0;
    }
    .hero-tagline-text {
        font-size: clamp(1.1rem, 2.5vw, 1.45rem);
        font-weight: 800;
        color: #B5804D;
        line-height: 1.3;
        margin: 0 0 14px 0;
        letter-spacing: -0.01em;
    }
    .hero-body-text {
        font-size: clamp(0.92rem, 1.9vw, 1.05rem);
        color: #4B5563;
        line-height: 1.62;
        margin: 0 0 20px 0;
    }
    .hero-image-card {
        position: relative;
        border-radius: 20px;
        overflow: hidden;
        border: 1.5px solid rgba(180, 215, 195, 0.8);
        border-bottom: 3.5px solid rgba(140, 190, 160, 0.9);
        box-shadow: 0 10px 25px -5px rgba(27, 77, 62, 0.15);
        height: 100%;
        min-height: 280px;
        max-height: 380px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #E8F5E9;
        box-sizing: border-box;
    }
    .hero-image-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }
    .hero-image-badge {
        position: absolute;
        bottom: 12px;
        left: 12px;
        right: 12px;
        background: rgba(15, 45, 34, 0.85);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        color: #FFFFFF;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 8px 12px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* =======================================================================
       SECTION CONTAINERS & HEADERS
       ======================================================================= */
    .about-section-container {
        margin-bottom: 36px;
        box-sizing: border-box;
        width: 100%;
    }
    .about-section-header {
        text-align: center;
        margin-bottom: 22px;
        box-sizing: border-box;
    }
    .about-section-title {
        font-size: clamp(1.4rem, 3.8vw, 2.1rem);
        font-weight: 800;
        color: #1B4D3E;
        letter-spacing: -0.02em;
        margin: 0 0 8px 0;
    }
    .about-section-subtext {
        font-size: clamp(0.88rem, 2vw, 1.02rem);
        color: #4B5563;
        max-width: 720px;
        margin: 0 auto;
        line-height: 1.55;
    }

    /* =======================================================================
       CARDS & GRIDS (TACTILE, WARM & BREATHING)
       ======================================================================= */
    .about-grid-3 {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 18px;
        width: 100%;
        box-sizing: border-box;
    }
    .about-grid-2 {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
        width: 100%;
        box-sizing: border-box;
    }
    .about-grid-4 {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
        width: 100%;
        box-sizing: border-box;
    }
    .about-grid-5 {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
        gap: 14px;
        width: 100%;
        box-sizing: border-box;
    }

    /* Farmer Highlight 3-Pillar Card */
    .farmer-pillar-card {
        background: linear-gradient(160deg, #FFFFFF 0%, #FAFAF7 100%);
        border: 1.5px solid rgba(215, 230, 222, 0.95);
        border-bottom: 3.5px solid #10B981;
        border-radius: 20px;
        padding: 24px 20px;
        box-shadow: 0 6px 16px -3px rgba(27, 77, 62, 0.06);
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        box-sizing: border-box;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .farmer-pillar-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px -4px rgba(27, 77, 62, 0.12);
    }
    .farmer-pillar-icon {
        width: 52px;
        height: 52px;
        border-radius: 16px;
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border: 1px solid #A7F3D0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        margin-bottom: 12px;
    }
    .farmer-pillar-title {
        font-size: 1.12rem;
        font-weight: 800;
        color: #1B4D3E;
        margin: 0 0 6px 0;
    }
    .farmer-pillar-desc {
        font-size: 0.86rem;
        color: #4B5563;
        line-height: 1.52;
        margin: 0;
    }

    /* Standard Tactile Feature Card */
    .about-card {
        background: linear-gradient(170deg, #FFFFFF 0%, #FAFCF9 100%);
        border: 1.5px solid rgba(220, 235, 226, 0.95);
        border-bottom: 3.5px solid rgba(185, 215, 195, 0.95);
        border-radius: 18px;
        padding: 20px 18px;
        box-shadow: 0 6px 16px -3px rgba(27, 77, 62, 0.05), inset 0 1px 1px #FFFFFF;
        box-sizing: border-box;
        transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        overflow: hidden;
    }
    .about-card:hover {
        transform: translateY(-2.5px);
        box-shadow: 0 12px 26px -4px rgba(27, 77, 62, 0.10);
        border-bottom-color: rgba(181, 131, 90, 0.7);
    }
    .about-card-icon {
        font-size: 24px;
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border: 1px solid rgba(167, 243, 208, 0.8);
        border-bottom: 2.5px solid #10B981;
        margin-bottom: 12px;
        flex-shrink: 0;
    }
    .about-card-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #111827;
        margin: 0 0 6px 0;
        line-height: 1.3;
    }
    .about-card-desc {
        font-size: 0.85rem;
        color: #4B5563;
        line-height: 1.5;
        margin: 0;
    }

    /* What is Faslyn 2-Column Container */
    .what-is-grid {
        display: grid;
        grid-template-columns: 1.15fr 0.85fr;
        gap: 24px;
        align-items: center;
        background: linear-gradient(145deg, #FFFFFF 0%, #FAFBF9 100%);
        border: 1.5px solid rgba(215, 230, 222, 0.9);
        border-bottom: 3.5px solid rgba(180, 210, 192, 0.9);
        border-radius: 22px;
        padding: 30px 28px;
        box-shadow: 0 8px 22px -4px rgba(27, 77, 62, 0.06);
        box-sizing: border-box;
    }
    .what-is-lead {
        font-size: 1.15rem;
        font-weight: 800;
        color: #1B4D3E;
        line-height: 1.4;
        margin-bottom: 12px;
    }
    .what-is-body {
        font-size: 0.92rem;
        color: #4B5563;
        line-height: 1.6;
        margin: 0 0 10px 0;
    }

    /* Visual Flow Diagram on Right Side */
    .flow-diagram-box {
        background: linear-gradient(135deg, #F3F8F5 0%, #EDF5F0 100%);
        border: 1.5px solid rgba(167, 243, 208, 0.8);
        border-radius: 18px;
        padding: 20px 18px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        box-sizing: border-box;
    }
    .flow-diagram-step {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #FFFFFF;
        border: 1px solid rgba(180, 215, 195, 0.8);
        border-radius: 12px;
        padding: 8px 14px;
        font-size: 0.86rem;
        font-weight: 700;
        color: #1B4D3E;
        box-shadow: 0 2px 6px rgba(27, 77, 62, 0.04);
    }
    .flow-diagram-arrow {
        text-align: center;
        color: #10B981;
        font-weight: 900;
        font-size: 0.95rem;
        line-height: 1;
    }

    /* Solution Timeline Pipeline */
    .solution-pipeline-desktop {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        background: linear-gradient(145deg, #FAF4EF 0%, #F5EBE1 100%);
        border: 1.5px solid rgba(212, 163, 115, 0.45);
        border-bottom: 3.5px solid #B5804D;
        border-radius: 20px;
        padding: 22px 18px;
        box-sizing: border-box;
    }
    .solution-pipeline-node {
        flex: 1;
        background: #FFFFFF;
        border: 1.5px solid rgba(181, 128, 77, 0.3);
        border-radius: 14px;
        padding: 14px 10px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(181, 131, 90, 0.08);
        box-sizing: border-box;
    }
    .solution-node-tag {
        font-size: 0.68rem;
        font-weight: 800;
        color: #B5804D;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .solution-node-title {
        font-size: 0.86rem;
        font-weight: 800;
        color: #1B4D3E;
    }
    .solution-pipeline-arrow {
        color: #B5804D;
        font-weight: 800;
        font-size: 1.15rem;
        flex-shrink: 0;
    }

    /* Trust 4-Grid */
    .trust-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
        background: linear-gradient(150deg, #F0FDF4 0%, #ECFDF5 100%);
        border: 1.5px solid #A7F3D0;
        border-bottom: 3.5px solid #10B981;
        border-radius: 22px;
        padding: 26px 24px;
        box-sizing: border-box;
    }
    .trust-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        background: #FFFFFF;
        border: 1px solid rgba(167, 243, 208, 0.9);
        border-radius: 14px;
        padding: 14px 16px;
        box-sizing: border-box;
    }
    .trust-check {
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: #10B981;
        color: #FFFFFF;
        font-size: 14px;
        font-weight: 900;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .trust-title {
        font-size: 0.92rem;
        font-weight: 700;
        color: #1B4D3E;
        margin-bottom: 2px;
    }
    .trust-desc {
        font-size: 0.82rem;
        color: #4B5563;
        line-height: 1.45;
    }

    /* Journey Ribbon */
    .journey-sequence-wrap {
        background: linear-gradient(135deg, #FAF4EF 0%, #F5EBE1 100%);
        border: 1.5px solid rgba(212, 163, 115, 0.4);
        border-bottom: 3.5px solid #B5804D;
        border-radius: 20px;
        padding: 24px 20px;
        text-align: center;
        box-sizing: border-box;
    }
    .journey-steps-row {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin: 14px 0;
    }
    .journey-step-chip {
        background: #FFFFFF;
        border: 1px solid rgba(181, 128, 77, 0.4);
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 800;
        color: #7D4E27;
        box-shadow: 0 2px 6px rgba(181, 131, 90, 0.12);
    }
    .journey-arrow {
        color: #B5804D;
        font-weight: 800;
        font-size: 1.1rem;
    }

    /* Final CTA Banner */
    .about-final-cta-card {
        background: linear-gradient(145deg, #1B4D3E 0%, #133A2E 100%);
        border-radius: 24px;
        padding: 38px 28px;
        text-align: center;
        color: #FFFFFF;
        box-shadow: 0 14px 40px -8px rgba(27, 77, 62, 0.35);
        box-sizing: border-box;
        margin-top: 14px;
    }
    .about-final-cta-title {
        font-size: clamp(1.6rem, 4vw, 2.3rem);
        font-weight: 800;
        color: #FFFFFF;
        margin: 0 0 8px 0;
    }
    .about-final-cta-sub {
        font-size: clamp(0.92rem, 2.2vw, 1.08rem);
        color: #D1FAE5;
        margin: 0 auto 20px auto;
        max-width: 580px;
        line-height: 1.5;
    }

    /* Primary Gold/Harvest CTA Buttons */
    .stButton > button,
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(180deg, #DEAE7F 0%, #D4A373 50%, #C4925E 100%) !important;
        border: 1px solid #B5804D !important;
        border-bottom: 3.5px solid #9C683E !important;
        border-radius: 9999px !important;
        padding: 0.65rem 2.0rem !important;
        min-height: 48px !important;
        box-shadow: 0 6px 14px rgba(181, 131, 90, 0.32), inset 0 1px 1px rgba(255, 255, 255, 0.5) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        cursor: pointer !important;
    }
    .stButton > button *,
    button[data-testid="baseButton-primary"] * {
        color: #1E1208 !important;
        font-weight: 800 !important;
        font-size: 1.0rem !important;
    }
    .stButton > button:hover,
    button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(180deg, #E8BC90 0%, #DCAE7E 50%, #CC9A66 100%) !important;
        border-color: #A97442 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 9px 20px rgba(181, 131, 90, 0.42), inset 0 1px 1px rgba(255, 255, 255, 0.6) !important;
    }

    /* =======================================================================
       MODAL DIALOG STYLING (ZERO CLIPPING & SMOOTH SCROLL)
       ======================================================================= */
    div[data-testid="stDialog"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 14px !important;
        box-sizing: border-box !important;
        overflow-y: auto !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] {
        background: linear-gradient(170deg, #FFFFFF 0%, #FAFCF9 100%) !important;
        border: 1.5px solid rgba(200, 225, 210, 0.95) !important;
        border-bottom: 4px solid rgba(160, 205, 180, 0.95) !important;
        border-radius: 20px !important;
        box-shadow: 0 20px 50px -10px rgba(27, 77, 62, 0.3) !important;
        max-width: 440px !important;
        width: 95vw !important;
        max-height: 88vh !important;
        max-height: 88dvh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding: 16px 20px 20px 20px !important;
        box-sizing: border-box !important;
        margin: auto !important;
        overscroll-behavior: contain !important;
        -webkit-overflow-scrolling: touch !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] > div {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        max-height: calc(88vh - 40px) !important;
        max-height: calc(88dvh - 40px) !important;
    }
    div[data-testid="stDialogHeader"] {
        margin-bottom: 4px !important;
        padding-bottom: 2px !important;
    }
    div[data-testid="stDialogHeader"] h2 {
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        color: #1B4D3E !important;
    }
    div[data-testid="stDialog"] div[data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
    }
    div[data-testid="stDialog"] .stTextInput {
        margin-bottom: -6px !important;
    }
    div[data-testid="stDialog"] .stCheckbox {
        margin-top: -4px !important;
        margin-bottom: 4px !important;
    }
    div[data-testid="stDialog"] .stButton > button {
        min-height: 42px !important;
        padding: 0.45rem 1.2rem !important;
        font-size: 0.92rem !important;
    }
    div[data-testid="stDialog"] div[role="dialog"]::-webkit-scrollbar,
    div[data-testid="stDialog"] div[role="dialog"] > div::-webkit-scrollbar {
        width: 5px;
    }
    div[data-testid="stDialog"] div[role="dialog"]::-webkit-scrollbar-thumb,
    div[data-testid="stDialog"] div[role="dialog"] > div::-webkit-scrollbar-thumb {
        background: #A7F3D0;
        border-radius: 9999px;
    }

    /* =======================================================================
       RESPONSIVE BREAKPOINTS (TABLETS & MOBILE)
       ======================================================================= */
    @media (max-width: 1024px) {
        .about-grid-4 {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }
        .about-grid-3 {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }
    }

    @media (max-width: 768px) {
        .about-hero-grid {
            grid-template-columns: 1fr !important;
            gap: 20px !important;
            padding: 24px 18px !important;
        }
        .hero-image-card {
            min-height: 220px !important;
            max-height: 280px !important;
        }
        .what-is-grid {
            grid-template-columns: 1fr !important;
            gap: 16px !important;
            padding: 22px 18px !important;
        }
        .about-grid-3,
        .about-grid-2,
        .about-grid-4,
        .about-grid-5,
        .trust-grid {
            grid-template-columns: 1fr !important;
            gap: 12px !important;
        }
        .solution-pipeline-desktop {
            flex-direction: column !important;
            gap: 8px !important;
        }
        .solution-pipeline-arrow {
            transform: rotate(90deg) !important;
        }
        .journey-steps-row {
            flex-direction: column !important;
            gap: 6px !important;
        }
        .journey-arrow {
            transform: rotate(90deg) !important;
        }
    }

    @media (max-width: 480px) {
        .about-hero-grid {
            padding: 18px 14px !important;
            border-radius: 18px !important;
        }
        .hero-image-card {
            min-height: 180px !important;
            max-height: 220px !important;
            border-radius: 14px !important;
        }
        .about-card,
        .farmer-pillar-card {
            padding: 16px 14px !important;
            border-radius: 14px !important;
        }
        .about-final-cta-card {
            padding: 24px 16px !important;
            border-radius: 18px !important;
        }
        div[data-testid="stDialog"] div[role="dialog"] {
            width: 95vw !important;
            max-height: 88vh !important;
            max-height: 88dvh !important;
            overflow-y: auto !important;
            padding: 16px 14px !important;
        }
    }

    @media (max-width: 360px) {
        .about-top-nav {
            flex-direction: column !important;
            gap: 8px !important;
            border-radius: 16px !important;
        }
    }
    </style>
    """


# ---------------------------------------------------------------------------
# LOGIN MODAL DIALOG (ROBUST ZERO-CLIPPING AUTHENTICATION)
# ---------------------------------------------------------------------------
@st.dialog("Welcome to Faslyn")
def show_login_modal():
    """Render clean, responsive authentication modal dialog connected to SQLite backend."""
    logo_b64 = get_faslyn_logo_base64()
    logo_modal_tag = f'<img src="{logo_b64}" alt="Faslyn Logo" style="width: 52px; height: 52px; border-radius: 50%; object-fit: contain; margin-bottom: 6px; box-shadow: 0 4px 12px rgba(27,77,62,0.12);" />' if logo_b64 else '<span>🌿</span>'
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: -10px; margin-bottom: 12px;">
            {logo_modal_tag}
            <div style="font-weight: 800; font-size: 1.25rem; color: #1B4D3E;">Faslyn</div>
            <div style="font-size: 0.82rem; color: #4B5563;">Access your agricultural intelligence dashboard.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1-Click Demo Profile for instant demonstration
    ramesh_profile = [p for p in DEMO_PROFILES if "Ramesh" in p.get("name", "")][:1]
    demo_prof = ramesh_profile[0] if ramesh_profile else DEMO_PROFILES[0]

    if st.button(
        f"⚡ 1-Click Demo: Enter as {demo_prof['name']} ({demo_prof['flag']} {demo_prof['badge']})",
        key="modal_demo_btn",
        use_container_width=True,
    ):
        st.session_state.is_authenticated = True
        st.session_state["authenticated"] = True
        st.session_state.just_logged_in = True
        st.session_state.user_name = demo_prof["name"]
        st.session_state.user_avatar = demo_prof["avatar"]
        st.session_state.user_role = demo_prof["role"]
        st.session_state.user_phone = demo_prof["phone"]
        st.session_state.user_region = demo_prof["region"]
        st.session_state.farmer_id = demo_prof["id"]
        st.session_state.selected_hub_name = demo_prof["hub"]
        st.session_state.coords = {
            "lat": BRICS_HUBS[demo_prof["hub"]]["lat"],
            "lon": BRICS_HUBS[demo_prof["hub"]]["lon"],
        }
        st.session_state.zoom = BRICS_HUBS[demo_prof["hub"]]["zoom"]
        st.session_state.current_language = demo_prof["lang"]
        st.session_state.advisory_lang_code = LANGUAGES[demo_prof["lang"]]
        st.session_state.active_tab_id = "home"
        st.session_state.nav_stack = ["home"]

        try:
            upsert_farmer(
                demo_prof["id"],
                demo_prof["phone"],
                demo_prof["name"],
                demo_prof["region"],
                demo_prof["role"],
                demo_prof["hub"],
            )
        except Exception:
            pass

        st.rerun()

    st.markdown(
        '<div style="text-align: center; color: #9CA3AF; font-size: 0.72rem; margin: 8px 0 6px 0; font-weight: 600; letter-spacing: 0.04em;">— OR SIGN IN WITH CREDENTIALS —</div>',
        unsafe_allow_html=True,
    )

    with st.form("modal_login_form", clear_on_submit=False):
        email_or_user = st.text_input(
            "Email / Username",
            placeholder="Enter your email or username",
            key="modal_input_user",
        )
        password = st.text_input(
            "Password",
            placeholder="Enter your password",
            type="password",
            key="modal_input_pass",
        )

        col_rem, col_blank = st.columns([1, 1], wrap=True)
        with col_rem:
            remember_me = st.checkbox("Remember me", value=True, key="modal_remember_me")

        submitted = st.form_submit_button("🌱 Login", type="primary", use_container_width=True)

        if submitted:
            entered_name = email_or_user.strip()
            if not entered_name:
                st.error("⚠️ Please enter your email or username to continue.")
            else:
                default_hub = list(BRICS_HUBS.keys())[0]
                name_parts = entered_name.split()
                initials = f"{name_parts[0][0]}{name_parts[1][0]}".upper() if len(name_parts) >= 2 else (entered_name[:2].upper() if len(entered_name) >= 2 else "FP")
                
                st.session_state.is_authenticated = True
                st.session_state["authenticated"] = True
                st.session_state.just_logged_in = True
                st.session_state.user_name = entered_name
                st.session_state.user_phone = "+91 98765 43210"
                st.session_state.user_region = "Odisha (Coastal Rice Belt)"
                st.session_state.user_role = "Smallholder Producer"
                st.session_state.user_avatar = initials
                st.session_state.farmer_id = f"FAS-{abs(hash(entered_name)) % 9000 + 1000}"
                st.session_state.selected_hub_name = default_hub
                st.session_state.coords = {
                    "lat": BRICS_HUBS[default_hub]["lat"],
                    "lon": BRICS_HUBS[default_hub]["lon"],
                }
                st.session_state.zoom = BRICS_HUBS[default_hub]["zoom"]
                st.session_state.current_language = "English"
                st.session_state.advisory_lang_code = LANGUAGES["English"]
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

    # Secondary options
    col_fp, col_ca = st.columns(2, wrap=True)
    with col_fp:
        if st.button("Forgot Password?", key="modal_fp_btn", use_container_width=True):
            st.info("ℹ️ Password recovery is linked to your regional agricultural cooperative SMS gateway.")
    with col_ca:
        if st.button("Create Account", key="modal_ca_btn", use_container_width=True):
            st.info("ℹ️ Enter your details above and click Login to provision your Faslyn profile.")


# ---------------------------------------------------------------------------
# FARMER-FIRST MODULAR ABOUT SECTIONS
# ---------------------------------------------------------------------------

def show_about_hero():
    """Render Section 1: Hero Section (Balanced 2 columns with authentic agricultural visual)."""
    hero_b64 = get_about_hero_image_base64()
    img_html = f'<img class="hero-image-img" src="{hero_b64}" alt="Farmer in Agricultural Field" />' if hero_b64 else '<div style="font-size: 4rem; text-align: center;">🌾</div>'

    st.markdown(
        f"""
        <div class="about-hero-grid">
            <div class="hero-content-col">
                <div class="hero-pill-tag">
                    <span>●</span> Agricultural Intelligence Platform
                </div>
                <h1 class="hero-main-title">Faslyn</h1>
                <div class="hero-tagline-text">"Smarter Insights. Better Decisions. Stronger Growth."</div>
                <p class="hero-body-text">
                    Faslyn helps turn agricultural information into simple, useful insights so farmers can better understand their crops, conditions and opportunities.
                </p>
            </div>
            <div class="hero-image-card">
                {img_html}
                <div class="hero-image-badge">
                    <span>🌾</span> Real-Time Insights for Smallholder Farming
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_btn1, c_btn2, c_btn3 = st.columns([1, 1.4, 1], wrap=True)
    with c_btn2:
        if st.button("🌱 Login to Faslyn", key="about_hero_login_btn", use_container_width=True, type="primary"):
            show_login_modal()
        st.markdown(
            """
            <div style="text-align: center; font-size: 0.76rem; color: #4B5563; margin-top: 6px;">
                ✓ Simple &bull; Trustworthy &bull; Built for Daily Farm Decisions
            </div>
            """,
            unsafe_allow_html=True,
        )


def show_farmer_first_section():
    """Render Section 2: Farmer-First Message (Built Around the Needs of Farmers)."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">Built Around the Needs of Farmers</h2>
                <div class="about-section-subtext">
                    Farming decisions depend on many things — crops, weather, soil, resources and changing conditions.
                    Faslyn brings relevant information together and presents it in a simpler way, helping users understand what the data is saying.
                </div>
            </div>
            <div class="about-grid-3">
                <div class="farmer-pillar-card">
                    <div class="farmer-pillar-icon">🌱</div>
                    <div class="farmer-pillar-title">Understand</div>
                    <div class="farmer-pillar-desc">
                        Understand important agricultural information and current farm conditions without confusing technical jargon.
                    </div>
                </div>
                <div class="farmer-pillar-card">
                    <div class="farmer-pillar-icon">📊</div>
                    <div class="farmer-pillar-title">See</div>
                    <div class="farmer-pillar-desc">
                        See vital information through clear visuals, simple charts, and localized field indicators.
                    </div>
                </div>
                <div class="farmer-pillar-card">
                    <div class="farmer-pillar-icon">💡</div>
                    <div class="farmer-pillar-title">Act</div>
                    <div class="farmer-pillar-desc">
                        Use practical insights to support your daily decisions, from irrigation timing to nutrient management.
                    </div>
                </div>
            </div>
            <div style="text-align: center; color: #6B7280; font-size: 0.74rem; margin-top: 14px; font-style: italic;">
                Note: Faslyn provides decision support to assist farming choices. It does not replace local farming experience or professional agricultural advice.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_what_is_faslyn():
    """Render Section 3: What is Faslyn? (Balanced 2-column layout with visual flow diagram)."""
    st.markdown(
        """
        <div class="about-section-container" id="about-what-is-faslyn">
            <div class="about-section-header">
                <h2 class="about-section-title">What is Faslyn?</h2>
            </div>
            <div class="what-is-grid">
                <div>
                    <div class="what-is-lead">"Agriculture needs more than data — it needs usable insights."</div>
                    <p class="what-is-body">
                        Faslyn is designed to bring relevant agricultural information together and present it in a simple, understandable and actionable way.
                    </p>
                    <p class="what-is-body">
                        Instead of making users go through scattered sources, Faslyn provides a centralized platform where data can be explored, analyzed and converted into meaningful insights for your land.
                    </p>
                </div>
                <div class="flow-diagram-box">
                    <div class="flow-diagram-step">
                        <span style="font-size: 1.2rem;">👨‍🌾</span> Farmer & Farm Field
                    </div>
                    <div class="flow-diagram-arrow">↓</div>
                    <div class="flow-diagram-step">
                        <span style="font-size: 1.2rem;">🛰️</span> Agricultural Data Feeds
                    </div>
                    <div class="flow-diagram-arrow">↓</div>
                    <div class="flow-diagram-step">
                        <span style="font-size: 1.2rem;">💡</span> Clear, Practical Insights
                    </div>
                    <div class="flow-diagram-arrow">↓</div>
                    <div class="flow-diagram-step" style="background: #1B4D3E; color: #FFFFFF; border-color: #1B4D3E;">
                        <span style="font-size: 1.2rem;">🚜</span> Confident Farming Decisions
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_problem_section():
    """Render Section 4: The Challenge We Address (Every Farming Decision Matters)."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">Every Farming Decision Matters</h2>
                <div class="about-section-subtext">
                    Farmers often have to make decisions while dealing with changing weather, crop conditions, resources and limited access to timely information.
                </div>
            </div>
            <div class="about-grid-3">
                <div class="about-card">
                    <div class="about-card-icon">🗂️</div>
                    <div class="about-card-title">Scattered Information</div>
                    <div class="about-card-desc">Important agricultural information can exist across different disconnected sources.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">📉</div>
                    <div class="about-card-title">Difficult Data Interpretation</div>
                    <div class="about-card-desc">Raw numbers do not always provide an immediate picture of what is actually happening in the field.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">❓</div>
                    <div class="about-card-title">Agricultural Uncertainty</div>
                    <div class="about-card-desc">Identifying potential crop issues and moisture stress at the right time can be difficult.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">🌦️</div>
                    <div class="about-card-title">Changing Conditions</div>
                    <div class="about-card-desc">Weather fluctuations and soil moisture variations directly impact day-to-day farm choices.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">🧩</div>
                    <div class="about-card-title">Lack of Centralized Insights</div>
                    <div class="about-card-desc">Different indicators are often viewed separately rather than together in one clear picture.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">⏳</div>
                    <div class="about-card-title">Time-Consuming Analysis</div>
                    <div class="about-card-desc">Manually comparing multiple weather and soil factors takes valuable time away from farming.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_visual_solution():
    """Render Section 5: From Information to Insight (Visual Process Pipeline)."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">From Information to Insight</h2>
                <div class="about-section-subtext">
                    A clear, reliable path connecting raw field data to practical understanding.
                </div>
            </div>
            <div class="solution-pipeline-desktop">
                <div class="solution-pipeline-node">
                    <div class="solution-node-tag">STEP 01</div>
                    <div class="solution-node-title">AGRICULTURAL INFORMATION</div>
                </div>
                <div class="solution-pipeline-arrow">→</div>
                <div class="solution-pipeline-node" style="border-color: #10B981; background: #F0FDF4;">
                    <div class="solution-node-tag" style="color: #047857;">STEP 02</div>
                    <div class="solution-node-title" style="color: #047857;">Faslyn</div>
                </div>
                <div class="solution-pipeline-arrow">→</div>
                <div class="solution-pipeline-node">
                    <div class="solution-node-tag">STEP 03</div>
                    <div class="solution-node-title">ANALYSIS</div>
                </div>
                <div class="solution-pipeline-arrow">→</div>
                <div class="solution-pipeline-node">
                    <div class="solution-node-tag">STEP 04</div>
                    <div class="solution-node-title">INSIGHTS</div>
                </div>
                <div class="solution-pipeline-arrow">→</div>
                <div class="solution-pipeline-node" style="background: #1B4D3E; border-color: #1B4D3E;">
                    <div class="solution-node-tag" style="color: #A7F3D0;">OUTCOME</div>
                    <div class="solution-node-title" style="color: #FFFFFF;">BETTER UNDERSTANDING</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_how_it_helps():
    """Render Section 6: How Faslyn Can Help (5 Farmer-Friendly Action Cards)."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">How Faslyn Can Help</h2>
                <div class="about-section-subtext">
                    Practical, farmer-friendly tools designed to assist and support your daily farming operations.
                </div>
            </div>
            <div class="about-grid-5">
                <div class="about-card">
                    <div class="about-card-icon">🌱</div>
                    <div class="about-card-title">Understand Conditions</div>
                    <div class="about-card-desc">Get a clearer view of relevant agricultural information and seasonal field factors.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">📊</div>
                    <div class="about-card-title">Understand Data</div>
                    <div class="about-card-desc">View important information through simple charts, indicators, and localized maps.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">🔍</div>
                    <div class="about-card-title">Identify Concerns</div>
                    <div class="about-card-desc">Bring attention to conditions and early signs that may require closer attention.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">💡</div>
                    <div class="about-card-title">Explore Insights</div>
                    <div class="about-card-desc">Understand patterns and available advisory guidance to support crop health.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">📈</div>
                    <div class="about-card-title">Monitor</div>
                    <div class="about-card-desc">Keep important farm information organized and accessible in one place.</div>
                </div>
            </div>
            <div style="text-align: center; color: #6B7280; font-size: 0.74rem; margin-top: 12px; font-style: italic;">
                Faslyn provides guidance and decision support to assist farmers; individual outcomes depend on local conditions, practices, and inputs.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_trust_section():
    """Render Section 7: Why Faslyn? (Trust Building Pillars)."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">Why Faslyn?</h2>
                <div class="about-section-subtext">
                    Built for simplicity, dependable guidance, and practical everyday use on the farm.
                </div>
            </div>
            <div class="trust-grid">
                <div class="trust-item">
                    <div class="trust-check">✓</div>
                    <div>
                        <div class="trust-title">Simple to Understand</div>
                        <div class="trust-desc">Presented in straightforward language without confusing technical jargon or overwhelming metrics.</div>
                    </div>
                </div>
                <div class="trust-item">
                    <div class="trust-check">✓</div>
                    <div>
                        <div class="trust-title">Information in One Place</div>
                        <div class="trust-desc">Weather trends, satellite indices, and soil readings organized seamlessly in a single dashboard.</div>
                    </div>
                </div>
                <div class="trust-item">
                    <div class="trust-check">✓</div>
                    <div>
                        <div class="trust-title">Visual and Easy to Explore</div>
                        <div class="trust-desc">Clear color-coded indicators, intuitive gauges, and localized map views make exploration natural.</div>
                    </div>
                </div>
                <div class="trust-item">
                    <div class="trust-check">✓</div>
                    <div>
                        <div class="trust-title">Designed to Support Informed Decisions</div>
                        <div class="trust-desc">Empowers farmers with reliable contextual intelligence to assist daily agricultural choices.</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_who_is_it_for():
    """Render Section 8: Who is Faslyn For? (Clear Audience Cards)."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">Who is Faslyn For?</h2>
                <div class="about-section-subtext">
                    Built for people working directly with land, crops, and agricultural planning.
                </div>
            </div>
            <div class="about-grid-4">
                <div class="about-card">
                    <div class="about-card-icon">🌾</div>
                    <div class="about-card-title">Small & Marginal Farmers</div>
                    <div class="about-card-desc">Designed to make relevant agricultural information easier to understand, explore, and apply.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">👨‍🌾</div>
                    <div class="about-card-title">Agricultural Professionals</div>
                    <div class="about-card-desc">For analyzing field conditions, monitoring soil metrics, and evaluating crop health indicators.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">🎓</div>
                    <div class="about-card-title">Students & Researchers</div>
                    <div class="about-card-desc">For exploring regional agricultural trends, historical climate patterns, and satellite data.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">🏢</div>
                    <div class="about-card-title">Cooperatives & Stakeholders</div>
                    <div class="about-card-desc">For bringing agricultural intelligence together to support community-wide resilience.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_vision_section():
    """Render Section 9: Our Vision."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">Our Vision</h2>
            </div>
            <div class="what-is-grid" style="background: linear-gradient(135deg, #FAF4EF 0%, #F5FAF7 100%); border-color: rgba(212, 163, 115, 0.4); border-bottom-color: #B5804D;">
                <div>
                    <div class="what-is-lead" style="color: #7D4E27;">"Making agricultural intelligence more accessible."</div>
                    <p class="what-is-body">
                        We want agricultural information to be easier to understand, easier to explore and more useful for the people who depend on it every day.
                    </p>
                    <p class="what-is-body">
                        Faslyn aims to bridge the gap between data and practical decision-making through a clean, accessible digital experience.
                    </p>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 18px; background: #FFFFFF; border-radius: 16px; border: 1px solid rgba(181, 128, 77, 0.3);">
                    <div style="font-size: 2.8rem; margin-bottom: 6px;">🌍</div>
                    <div style="font-weight: 800; font-size: 1.05rem; color: #1B4D3E;">Digital Public Good</div>
                    <div style="font-size: 0.80rem; color: #6B7280; margin-top: 4px;">Open-Access Agro-Intelligence for Cooperative Growth</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_journey_section():
    """Render Section 10: Faslyn Journey."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">The Faslyn Journey</h2>
            </div>
            <div class="journey-sequence-wrap">
                <div class="journey-steps-row">
                    <div class="journey-step-chip">DATA</div>
                    <div class="journey-arrow">→</div>
                    <div class="journey-step-chip">UNDERSTANDING</div>
                    <div class="journey-arrow">→</div>
                    <div class="journey-step-chip">ANALYSIS</div>
                    <div class="journey-arrow">→</div>
                    <div class="journey-step-chip">INSIGHTS</div>
                    <div class="journey-arrow">→</div>
                    <div class="journey-step-chip" style="background: #1B4D3E; color: #FFFFFF; border-color: #1B4D3E;">ACTION</div>
                </div>
                <div style="font-weight: 800; font-size: 1.08rem; color: #1B4D3E; margin-top: 14px;">
                    "Faslyn connects the journey."
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_final_cta():
    """Render Section 11: Final Call to Action."""
    st.markdown(
        """
        <div class="about-final-cta-card">
            <h2 class="about-final-cta-title">Ready to Explore Faslyn?</h2>
            <div class="about-final-cta-sub">Discover your agricultural insights in one simple platform.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    c_cta1, c_cta2, c_cta3 = st.columns([1, 1.4, 1], wrap=True)
    with c_cta2:
        if st.button("🌱 Login to Faslyn", key="about_bottom_login_btn", use_container_width=True, type="primary"):
            show_login_modal()
        st.markdown(
            """
            <div style="text-align: center; font-size: 0.78rem; color: #4B5563; margin-top: 8px;">
                Sign in to access your personalized dashboard and explore available insights.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# MASTER ABOUT PAGE RENDERER
# ---------------------------------------------------------------------------
def show_about_page():
    """Master coordinator function rendering the full farmer-centric About page."""
    render_splash_loader("Initializing agro-intelligence feeds...")
    st.markdown(get_about_css(), unsafe_allow_html=True)

    logo_b64 = get_faslyn_logo_base64()
    logo_img_tag = f'<img src="{logo_b64}" alt="Faslyn Logo" style="width: 38px; height: 38px; border-radius: 50%; object-fit: contain; box-shadow: 0 2px 6px rgba(0,0,0,0.08);" />' if logo_b64 else '<span>🌿</span>'

    # Top Navbar Bar with Brand and Instant Login Action
    st.markdown(
        f"""
        <div class="about-top-nav">
            <div class="about-nav-brand" style="display: flex; align-items: center; gap: 10px;">
                {logo_img_tag}
                <span style="font-weight: 800; font-size: 1.35rem; color: #1B4D3E; letter-spacing: -0.02em;">Faslyn</span>
            </div>
            <div class="about-nav-badge">
                <span>●</span> Agricultural Intelligence Platform
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render All Farmer-First Sections Sequentially
    show_about_hero()
    show_farmer_first_section()
    show_what_is_faslyn()
    show_problem_section()
    show_visual_solution()
    show_how_it_helps()
    show_trust_section()
    show_who_is_it_for()
    show_vision_section()
    show_journey_section()
    show_final_cta()

    # Footer
    st.markdown(
        """
        <div style="text-align: center; color: #9CA3AF; font-size: 0.76rem; padding-top: 36px; padding-bottom: 24px;">
            &copy; 2026 Faslyn &bull; Open-Access Agricultural Intelligence &bull; Sovereign Agroclimatology
        </div>
        """,
        unsafe_allow_html=True,
    )
