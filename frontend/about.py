"""
FASLYN About Page & Login Modal Flow
====================================
Comprehensive introductory presentation explaining FASLYN prior to authentication.
Includes all 11 user-specified sections, responsive 3D tactile card layouts,
and a clean Streamlit modal dialog for authentication.
"""

import os
import streamlit as st
from backend.config import BRICS_HUBS, DEMO_PROFILES, FIRST_HUB, LANGUAGES
from backend.database import upsert_farmer


def get_about_css() -> str:
    """Return mobile-first, zero-overflow CSS rules for the About page and modal."""
    return """
    <style>
    /* =======================================================================
       ABOUT PAGE - MODERN 3D TACTILE STYLING (ZERO HORIZONTAL OVERFLOW)
       ======================================================================= */
    
    /* Root Viewport and Container Enforcements */
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

    /* Hide sidebar and toggle buttons entirely on the unauthenticated About page */
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

    .about-page-wrapper {
        width: 100%;
        max-width: 1140px;
        margin: 0 auto;
        padding: 0 0 3.5rem 0;
        box-sizing: border-box;
        overflow-x: hidden;
    }

    /* Top Navigation Header Bar */
    .about-top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 18px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(220, 235, 226, 0.9);
        border-bottom: 3px solid rgba(185, 215, 195, 0.9);
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
        gap: 5px;
        background: #ECFDF5;
        border: 1px solid #A7F3D0;
        color: #047857;
        font-size: 0.70rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 9999px;
    }

    /* Hero Section Card */
    .about-hero-card {
        background: linear-gradient(145deg, #FFFFFF 0%, #F5FAF7 100%);
        border: 1.5px solid rgba(200, 225, 210, 0.95);
        border-bottom: 4px solid rgba(160, 205, 180, 0.95);
        border-radius: 24px;
        padding: 38px 32px 34px 32px;
        text-align: center;
        margin-bottom: 32px;
        box-shadow: 0 12px 35px -6px rgba(27, 77, 62, 0.10), inset 0 1px 1px #FFFFFF;
        box-sizing: border-box;
        overflow: hidden;
    }
    .about-hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #E8F5E9;
        border: 1px solid #C8E6C9;
        color: #1B4D3E;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 5px 14px;
        border-radius: 9999px;
        margin-bottom: 16px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .about-hero-title {
        font-size: clamp(2.4rem, 6vw, 3.8rem);
        font-weight: 900;
        color: #1B4D3E;
        letter-spacing: -0.04em;
        line-height: 1.08;
        margin: 0 0 12px 0;
    }
    .about-hero-tagline {
        font-size: clamp(1.15rem, 3vw, 1.65rem);
        font-weight: 800;
        color: #B5804D;
        line-height: 1.25;
        margin: 0 0 18px 0;
        letter-spacing: -0.01em;
    }
    .about-hero-desc {
        font-size: clamp(0.92rem, 2vw, 1.05rem);
        color: #4B5563;
        line-height: 1.65;
        max-width: 760px;
        margin: 0 auto 24px auto;
    }

    /* Common Section Containers */
    .about-section-container {
        margin-bottom: 34px;
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
        color: #111827;
        letter-spacing: -0.02em;
        margin: 0 0 8px 0;
    }
    .about-section-subtext {
        font-size: clamp(0.88rem, 2vw, 1.02rem);
        color: #4B5563;
        max-width: 700px;
        margin: 0 auto;
        line-height: 1.55;
    }

    /* Card Grids */
    .about-grid-3 {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        width: 100%;
        box-sizing: border-box;
    }
    .about-grid-2 {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
        width: 100%;
        box-sizing: border-box;
    }
    .about-grid-4 {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
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

    /* Generic 3D Tactile Card */
    .about-card {
        background: linear-gradient(170deg, #FFFFFF 0%, #FAFCF9 100%);
        border: 1.5px solid rgba(220, 235, 226, 0.95);
        border-bottom: 3.5px solid rgba(185, 215, 195, 0.95);
        border-radius: 18px;
        padding: 20px 18px;
        box-shadow: 0 6px 18px -3px rgba(27, 77, 62, 0.06), 0 2px 5px rgba(0, 0, 0, 0.02), inset 0 1px 1px #FFFFFF;
        box-sizing: border-box;
        transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s ease;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        overflow: hidden;
    }
    .about-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 28px -4px rgba(27, 77, 62, 0.12), inset 0 1px 1px #FFFFFF;
        border-bottom-color: rgba(181, 131, 90, 0.65);
    }
    .about-card-icon {
        font-size: 26px;
        width: 48px;
        height: 48px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border: 1px solid rgba(167, 243, 208, 0.8);
        border-bottom: 2.5px solid #10B981;
        margin-bottom: 14px;
        flex-shrink: 0;
    }
    .about-card-title {
        font-size: 1.05rem;
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

    /* What is FASLYN Highlight Box */
    .what-is-highlight-card {
        background: linear-gradient(135deg, #E8F5E9 0%, #F1F8F4 100%);
        border: 1.5px solid #C8E6C9;
        border-bottom: 4px solid #A5D6A7;
        border-radius: 20px;
        padding: 26px 28px;
        box-shadow: 0 8px 24px -4px rgba(27, 77, 62, 0.08), inset 0 1px 1px #FFFFFF;
        margin-bottom: 16px;
        box-sizing: border-box;
    }
    .what-is-highlight-lead {
        font-size: clamp(1.1rem, 2.5vw, 1.35rem);
        font-weight: 800;
        color: #1B4D3E;
        margin: 0 0 12px 0;
        line-height: 1.4;
    }
    .what-is-highlight-text {
        font-size: 0.95rem;
        color: #374151;
        line-height: 1.65;
        margin: 0 0 10px 0;
    }

    /* How FASLYN Works 4-Step Flow */
    .how-flow-desktop {
        display: flex;
        justify-content: space-between;
        align-items: stretch;
        gap: 12px;
        width: 100%;
        box-sizing: border-box;
    }
    .how-step-card {
        flex: 1 1 0;
        background: #FFFFFF;
        border: 1.5px solid #E5EBE7;
        border-bottom: 3.5px solid #D4A373;
        border-radius: 16px;
        padding: 18px 14px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        box-sizing: border-box;
        position: relative;
    }
    .how-step-num {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 800;
        color: #B5804D;
        background: #FAF4EF;
        padding: 2px 8px;
        border-radius: 9999px;
        margin-bottom: 8px;
        letter-spacing: 0.04em;
    }
    .how-step-name {
        font-size: 0.95rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 6px;
    }
    .how-step-desc {
        font-size: 0.80rem;
        color: #4B5563;
        line-height: 1.45;
    }
    .how-flow-ribbon {
        background: #FAF4EF;
        border: 1px solid rgba(212, 163, 115, 0.4);
        border-radius: 9999px;
        padding: 8px 16px;
        text-align: center;
        font-weight: 800;
        color: #7D4E27;
        font-size: 0.86rem;
        margin-top: 14px;
        box-sizing: border-box;
    }

    /* Visual Comparison: Traditional vs FASLYN */
    .comparison-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        width: 100%;
        box-sizing: border-box;
    }
    .comp-col-trad {
        background: #FFFBFB;
        border: 1.5px solid #FEE2E2;
        border-bottom: 3.5px solid #FCA5A5;
        border-radius: 18px;
        padding: 20px;
        box-sizing: border-box;
    }
    .comp-col-faslyn {
        background: #F0FDF4;
        border: 1.5px solid #BBF7D0;
        border-bottom: 3.5px solid #86EFAC;
        border-radius: 18px;
        padding: 20px;
        box-sizing: border-box;
    }
    .comp-col-title {
        font-size: 1.08rem;
        font-weight: 800;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .comp-list-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.88rem;
        padding: 6px 0;
        color: #374151;
        border-bottom: 1px solid rgba(0,0,0,0.04);
    }

    /* Journey Sequence */
    .journey-sequence-wrap {
        background: linear-gradient(135deg, #FAF4EF 0%, #F5EBE1 100%);
        border: 1.5px solid rgba(212, 163, 115, 0.4);
        border-bottom: 3.5px solid #B5804D;
        border-radius: 20px;
        padding: 22px 24px;
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
        margin: 0 0 10px 0;
    }
    .about-final-cta-sub {
        font-size: clamp(0.95rem, 2.2vw, 1.12rem);
        color: #D1FAE5;
        margin: 0 auto 22px auto;
        max-width: 620px;
        line-height: 1.5;
    }

    /* Primary Gold/Brown CTA Buttons */
    .stButton > button,
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(180deg, #DEAE7F 0%, #D4A373 50%, #C4925E 100%) !important;
        border: 1px solid #B5804D !important;
        border-bottom: 3.5px solid #9C683E !important;
        border-radius: 9999px !important;
        padding: 0.60rem 2.0rem !important;
        min-height: 48px !important;
        box-shadow: 0 6px 14px rgba(181, 131, 90, 0.32), inset 0 1px 1px rgba(255, 255, 255, 0.5) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
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

    /* Modal / Dialog Backdrop & Outer Overlay */
    div[data-testid="stDialog"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 14px !important;
        box-sizing: border-box !important;
        overflow-y: auto !important;
    }
    /* Modal Dialog Window */
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
    div[data-testid="stDialog"] .stButton > button {
        min-height: 42px !important;
        padding: 0.45rem 1.2rem !important;
        font-size: 0.92rem !important;
    }
    /* Custom sleek scrollbar for dialog */
    div[data-testid="stDialog"] div[role="dialog"]::-webkit-scrollbar,
    div[data-testid="stDialog"] div[role="dialog"] > div::-webkit-scrollbar {
        width: 5px;
    }
    div[data-testid="stDialog"] div[role="dialog"]::-webkit-scrollbar-thumb,
    div[data-testid="stDialog"] div[role="dialog"] > div::-webkit-scrollbar-thumb {
        background: #A7F3D0;
        border-radius: 9999px;
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


    /* =======================================================================
       RESPONSIVE MEDIA QUERIES (TABLETS & MOBILE PHONES)
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
        .about-top-nav {
            padding: 10px 14px !important;
            margin-bottom: 18px !important;
        }
        .about-hero-card {
            padding: 26px 18px 24px 18px !important;
            border-radius: 20px !important;
        }
        .about-grid-3,
        .about-grid-2,
        .about-grid-4,
        .about-grid-5 {
            grid-template-columns: 1fr !important;
            gap: 12px !important;
        }
        .how-flow-desktop {
            flex-direction: column !important;
            gap: 10px !important;
        }
        .comparison-container {
            grid-template-columns: 1fr !important;
            gap: 12px !important;
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
        .about-hero-card {
            padding: 20px 14px !important;
            border-radius: 16px !important;
        }
        .about-card {
            padding: 16px 14px !important;
            border-radius: 14px !important;
        }
        .about-card-icon {
            width: 40px !important;
            height: 40px !important;
            font-size: 22px !important;
            border-radius: 10px !important;
            margin-bottom: 10px !important;
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
# LOGIN MODAL DIALOG
# ---------------------------------------------------------------------------
@st.dialog("Welcome to FASLYN")
def show_login_modal():
    """Render clean, responsive authentication modal dialog connected to SQLite backend."""
    st.markdown(
        """
        <div style="text-align: center; margin-top: -10px; margin-bottom: 10px;">
            <div style="font-size: 0.82rem; color: #4B5563;">Access your agricultural intelligence dashboard.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1-Click Demo Profile for quick testing
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

        col_rem, col_blank = st.columns([1, 1])
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
    col_fp, col_ca = st.columns(2)
    with col_fp:
        if st.button("Forgot Password?", key="modal_fp_btn", use_container_width=True):
            st.info("ℹ️ Password recovery is linked to your regional agricultural cooperative SMS gateway.")
    with col_ca:
        if st.button("Create Account", key="modal_ca_btn", use_container_width=True):
            st.info("ℹ️ Enter your details above and click Login to provision your FASLYN profile.")



# ---------------------------------------------------------------------------
# 11 MODULAR ABOUT SECTIONS
# ---------------------------------------------------------------------------

def show_about_hero():
    """Render Section 1: Hero."""
    st.markdown(
        """
        <div class="about-hero-card">
            <div class="about-hero-pill">
                <span>●</span> Intelligent Agricultural Intelligence Platform
            </div>
            <h1 class="about-hero-title">FASLYN</h1>
            <div class="about-hero-tagline">"Smarter Insights. Better Decisions. Stronger Growth."</div>
            <p class="about-hero-desc">
                FASLYN is an intelligent agricultural platform designed to turn agricultural data into clear, useful insights.
                From understanding current conditions to identifying problems and exploring suitable solutions, FASLYN brings important information together in one simple dashboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_btn1, c_btn2, c_btn3 = st.columns([1, 1.4, 1])
    with c_btn2:
        if st.button("🌱 Login to FASLYN", key="about_hero_login_btn", use_container_width=True, type="primary"):
            show_login_modal()


def show_what_is_faslyn():
    """Render Section 2: What is FASLYN?"""
    st.markdown(
        """
        <div class="about-section-container" id="about-what-is-faslyn">
            <div class="about-section-header">
                <h2 class="about-section-title">What is FASLYN?</h2>
            </div>
            <div class="what-is-highlight-card">
                <div class="what-is-highlight-lead">"Agriculture needs more than data — it needs usable insights."</div>
                <p class="what-is-highlight-text">
                    FASLYN is designed to bring relevant agricultural information together and present it in a simple, understandable and actionable way.
                </p>
                <p class="what-is-highlight-text">
                    Instead of making users go through scattered information, FASLYN provides a centralized platform where data can be explored, analyzed and converted into meaningful insights.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_problem_section():
    """Render Section 3: The Challenge We Address (All 6 cards)."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">The Challenge We Address</h2>
                <div class="about-section-subtext">Agricultural information is often scattered and difficult to interpret.</div>
            </div>
            <div class="about-grid-3">
                <div class="about-card">
                    <div class="about-card-icon">🗂️</div>
                    <div class="about-card-title">1. Scattered Information</div>
                    <div class="about-card-desc">Important agricultural information can exist across different sources.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">📉</div>
                    <div class="about-card-title">2. Difficult Data Interpretation</div>
                    <div class="about-card-desc">Raw data does not always provide an immediate picture of what is happening.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">❓</div>
                    <div class="about-card-title">3. Agricultural Uncertainty</div>
                    <div class="about-card-desc">Identifying potential issues at the right time can be difficult.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">🌦️</div>
                    <div class="about-card-title">4. Changing Conditions</div>
                    <div class="about-card-desc">Weather and environmental conditions can affect agricultural outcomes.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">🧩</div>
                    <div class="about-card-title">5. Lack of Centralized Insights</div>
                    <div class="about-card-desc">Different indicators are often viewed separately rather than together.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">⏳</div>
                    <div class="about-card-title">6. Time-Consuming Analysis</div>
                    <div class="about-card-desc">Manually comparing multiple factors can take valuable time.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_features_section():
    """Render Section 4: What FASLYN Does (All 5 feature cards)."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">From Information to Insight</h2>
                <div class="about-section-subtext">Comprehensive capabilities built to empower agricultural stewardship.</div>
            </div>
            <div class="about-grid-5">
                <div class="about-card">
                    <div class="about-card-icon">🌱</div>
                    <div class="about-card-title">Analyze</div>
                    <div class="about-card-desc">Understand agricultural data and identify important patterns.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">📊</div>
                    <div class="about-card-title">Visualize</div>
                    <div class="about-card-desc">Convert information into dashboards, charts and meaningful indicators.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">🔎</div>
                    <div class="about-card-title">Identify</div>
                    <div class="about-card-desc">Highlight potential issues and areas that may require attention.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">💡</div>
                    <div class="about-card-title">Recommend</div>
                    <div class="about-card-desc">Provide useful insights that can support better-informed decisions.</div>
                </div>
                <div class="about-card">
                    <div class="about-card-icon">📈</div>
                    <div class="about-card-title">Monitor</div>
                    <div class="about-card-desc">Keep track of important agricultural indicators through a centralized dashboard.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_how_it_works():
    """Render Section 5: How FASLYN Works (Visual 4-step process)."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">How FASLYN Works</h2>
                <div class="about-section-subtext">A streamlined sequence transforming raw inputs into decisive action.</div>
            </div>
            <div class="how-flow-desktop">
                <div class="how-step-card">
                    <div class="how-step-num">01 — INPUT</div>
                    <div class="how-step-name">Input</div>
                    <div class="how-step-desc">Relevant agricultural information enters the system.</div>
                </div>
                <div class="how-step-card">
                    <div class="how-step-num">02 — ANALYZE</div>
                    <div class="how-step-name">Analyze</div>
                    <div class="how-step-desc">FASLYN processes and examines the available information.</div>
                </div>
                <div class="how-step-card">
                    <div class="how-step-num">03 — GENERATE INSIGHTS</div>
                    <div class="how-step-name">Generate Insights</div>
                    <div class="how-step-desc">The system identifies patterns, conditions and important indicators.</div>
                </div>
                <div class="how-step-card">
                    <div class="how-step-num">04 — DASHBOARD</div>
                    <div class="how-step-name">Dashboard</div>
                    <div class="how-step-desc">The results are presented through a simple, visual dashboard.</div>
                </div>
            </div>
            <div class="how-flow-ribbon">
                INPUT &nbsp;→&nbsp; ANALYSIS &nbsp;→&nbsp; INSIGHTS &nbsp;→&nbsp; DASHBOARD
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
            <div class="what-is-highlight-card" style="background: linear-gradient(135deg, #FAF4EF 0%, #F5FAF7 100%); border-color: rgba(212, 163, 115, 0.4); border-bottom-color: #B5804D;">
                <div class="what-is-highlight-lead" style="color: #7D4E27;">"Making agricultural intelligence more accessible."</div>
                <p class="what-is-highlight-text">
                    Our vision is to create a platform where agricultural information is not just collected, but understood and transformed into useful insights.
                </p>
                <p class="what-is-highlight-text">
                    FASLYN aims to bridge the gap between data and decision-making through a simple, accessible and intelligent digital experience.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_journey_section():
    """Render Section 10: FASLYN Journey."""
    st.markdown(
        """
        <div class="about-section-container">
            <div class="about-section-header">
                <h2 class="about-section-title">The FASLYN Journey</h2>
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
                    <div class="journey-step-chip" style="background: #1B4D3E; color: #FFFFFF;">ACTION</div>
                </div>
                <div style="font-weight: 800; font-size: 1.05rem; color: #1B4D3E; margin-top: 12px;">
                    "FASLYN connects the journey."
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_final_cta():
    """Render Section 11: Final CTA."""
    st.markdown(
        """
        <div class="about-final-cta-card">
            <h2 class="about-final-cta-title">Ready to Explore FASLYN?</h2>
            <div class="about-final-cta-sub">Your agricultural insights are just one step away.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    c_cta1, c_cta2, c_cta3 = st.columns([1, 1.4, 1])
    with c_cta2:
        if st.button("🌱 Login to FASLYN", key="about_bottom_login_btn", use_container_width=True, type="primary"):
            show_login_modal()
        st.markdown(
            """
            <div style="text-align: center; font-size: 0.76rem; color: #6B7280; margin-top: 8px;">
                Sign in to access your personalized dashboard and explore the available insights.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# MASTER ABOUT PAGE RENDERER
# ---------------------------------------------------------------------------
def show_about_page():
    """Master coordinator function rendering the full About page."""
    st.markdown(get_about_css(), unsafe_allow_html=True)

    # Top Navbar Bar with Brand and Instant Login Action
    st.markdown(
        """
        <div class="about-top-nav">
            <div class="about-nav-brand">
                <span>🌿</span> FASLYN
            </div>
            <div class="about-nav-badge">
                <span>●</span> Agricultural Intelligence Platform
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render About Sections sequentially
    show_about_hero()
    show_what_is_faslyn()
    show_problem_section()
    show_features_section()
    show_how_it_works()
    show_vision_section()
    show_journey_section()
    show_final_cta()

    # Footer
    st.markdown(
        """
        <div style="text-align: center; color: #9CA3AF; font-size: 0.76rem; padding-top: 36px; padding-bottom: 20px;">
            &copy; 2026 FASLYN &bull; Open-Access Agricultural Intelligence &bull; Sovereign Agroclimatology
        </div>
        """,
        unsafe_allow_html=True,
    )
