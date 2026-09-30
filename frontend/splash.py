"""
Faslyn High-Polish 3D Splash Preloader Module
=============================================
Provides a self-contained, zero-dependency 3D green & blue splash screen overlay
that displays on website startup and smoothly fades out after 2 seconds.
"""
import base64
import os
import streamlit as st


def get_splash_logo_base64() -> str:
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


def render_splash_loader(status_msg="Initializing agro-intelligence feeds...", force=False):
    """
    Render self-contained, high-polish 3D green & blue splash loader on startup.
    Features:
      - Fixed viewport overlay (z-index: 999999999)
      - 3D soft green-to-blue radial background
      - Animated gradient spinner with 🌱 sprout
      - Official circular Faslyn logo
      - Animated progress bar filling 0-100% in 1.85s
      - Smooth fade-out and auto-removal at 2.1s
    """
    if not force and st.session_state.get("has_shown_initial_splash", False):
        return

    st.session_state["has_shown_initial_splash"] = True
    logo_uri = get_splash_logo_base64()
    logo_tag = f'<img src="{logo_uri}" alt="Faslyn" />' if logo_uri else '<span>🌱</span>'

    loader_html = f"""
    <style>
    #faslyn-splash-loader {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        background: radial-gradient(circle at 45% 35%, #F0FDF4 0%, #E0F2FE 45%, #E6F7EE 75%, #DCEEFE 100%) !important;
        z-index: 999999999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        overflow: hidden !important;
        pointer-events: auto !important;
        animation: faslynSplashContainerFlow 3.3s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    }}
    #faslyn-splash-loader .faslyn-loader-card {{
        background: #FFFFFF !important;
        border: 1px solid rgba(220, 240, 230, 0.95) !important;
        border-bottom: 4px solid #10B981 !important;
        border-radius: 26px !important;
        padding: 34px 44px !important;
        box-shadow: 0 24px 60px -10px rgba(16, 114, 85, 0.18), 0 10px 24px -6px rgba(2, 132, 199, 0.14) !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        text-align: center !important;
        gap: 14px !important;
        max-width: 360px !important;
        width: 90% !important;
        box-sizing: border-box !important;
        animation: faslynSplashCardFlow 3.3s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
    }}
    #faslyn-splash-loader .faslyn-spinner-wrapper {{
        position: relative !important;
        width: 68px !important;
        height: 68px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-bottom: 4px !important;
    }}
    #faslyn-splash-loader .faslyn-spinner-ring {{
        position: absolute !important;
        width: 100% !important;
        height: 100% !important;
        border-radius: 50% !important;
        border: 3.5px solid rgba(16, 185, 129, 0.16) !important;
        border-top: 3.5px solid #10B981 !important;
        border-right: 3.5px solid #0284C7 !important;
        box-shadow: 0 3px 12px rgba(2, 132, 199, 0.20) !important;
        animation: faslynSplashSpin 0.65s linear infinite !important;
    }}
    #faslyn-splash-loader .faslyn-spinner-icon {{
        font-size: 28px !important;
        animation: faslynSplashPulse 0.8s ease-in-out infinite !important;
    }}
    #faslyn-splash-loader .faslyn-loader-brand {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 10px !important;
        font-size: 1.65rem !important;
        font-weight: 800 !important;
        color: #1B4D3E !important;
        letter-spacing: -0.5px !important;
    }}
    #faslyn-splash-loader .faslyn-loader-brand img {{
        width: 38px !important;
        height: 38px !important;
        border-radius: 50% !important;
        object-fit: contain !important;
    }}
    #faslyn-splash-loader .faslyn-loader-subtitle {{
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #4B5563 !important;
        margin-top: -4px !important;
    }}
    #faslyn-splash-loader .faslyn-loader-track {{
        width: 200px !important;
        height: 6px !important;
        background: rgba(2, 132, 199, 0.12) !important;
        border-radius: 9999px !important;
        overflow: hidden !important;
        margin-top: 4px !important;
    }}
    #faslyn-splash-loader .faslyn-loader-bar {{
        height: 100% !important;
        background: linear-gradient(90deg, #10B981 0%, #0284C7 50%, #34D399 100%) !important;
        border-radius: 9999px !important;
        animation: faslynSplashProgressFill 2.85s cubic-bezier(0.2, 0.7, 0.3, 1) forwards !important;
    }}
    #faslyn-splash-loader .faslyn-loader-status {{
        font-size: 0.74rem !important;
        font-weight: 600 !important;
        color: #6B7280 !important;
    }}
    @keyframes faslynSplashProgressFill {{
        0% {{ width: 0%; }}
        35% {{ width: 55%; }}
        75% {{ width: 88%; }}
        100% {{ width: 100%; }}
    }}
    @keyframes faslynSplashSpin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    @keyframes faslynSplashPulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.15); }}
    }}
    @keyframes faslynSplashCardFlow {{
        0% {{ transform: scale(0.92); opacity: 0; }}
        12% {{ transform: scale(1); opacity: 1; }}
        84% {{ transform: scale(1); opacity: 1; }}
        96% {{ transform: scale(1.08); opacity: 0; }}
        100% {{ transform: scale(1.08); opacity: 0; display: none !important; }}
    }}
    @keyframes faslynSplashContainerFlow {{
        0% {{ opacity: 1; visibility: visible; }}
        84% {{ opacity: 1; visibility: visible; }}
        96% {{ opacity: 0; visibility: hidden; pointer-events: none; }}
        100% {{ opacity: 0; visibility: hidden; pointer-events: none; display: none !important; }}
    }}
    </style>
    <div id="faslyn-splash-loader">
        <div class="faslyn-loader-card">
            <div class="faslyn-spinner-wrapper">
                <div class="faslyn-spinner-ring"></div>
                <div class="faslyn-spinner-icon">🌱</div>
            </div>
            <div class="faslyn-loader-brand">
                {logo_tag}
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
            var el = document.getElementById("faslyn-splash-loader");
            if (el) {{
                setTimeout(function() {{
                    el.style.transition = "opacity 0.35s ease, transform 0.35s ease";
                    el.style.opacity = "0";
                    el.style.pointerEvents = "none";
                    setTimeout(function() {{
                        if (el && el.parentNode) {{
                            el.parentNode.removeChild(el);
                        }}
                    }}, 350);
                }}, 3100);
            }}
        }} catch(e) {{}}
    }})();
    </script>
    """
    st.markdown(loader_html, unsafe_allow_html=True)
