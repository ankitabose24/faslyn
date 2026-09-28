"""
Faslyn — Frontend (Streamlit UI)
======================================
Faslyn = "Fasal" (crop) + "Link" (connection) — connecting crop data,
intelligence & farmers across BRICS.

Run from the project root with:
    streamlit run frontend/app.py

Designed for smallholder farmer accessibility:
- Zero-sensor: no expensive hardware needed
- Plain-language interpretations for soil & satellite metrics
- Multilingual spoken audio for low-literacy field access
- 1-click test samples for instant leaf disease diagnosis
- Aligned with BRICS AgriN & national digital agriculture standards
"""

import json
import os
import sys

# Make the project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from backend.ai_service import (
    GENAI_AVAILABLE,
    build_genai_client,
    generate_advisory,
    generate_crop_recommendation,
    generate_diagnosis,
)
from backend.config import BRICS_HUBS, FIRST_HUB, LANGUAGES
from backend.satellite_service import fetch_satellite_agroclimatology
from backend.telemetry_service import fetch_soil_telemetry
from frontend.tts import speak_text

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Faslyn | BRICS Regenerative Ag Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CUSTOM CSS FOR FARMER-FRIENDLY VISUALS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .metric-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 4px;
    }
    .badge-optimal { background-color: #d4edda; color: #155724; }
    .badge-warning { background-color: #fff3cd; color: #856404; }
    .badge-alert { background-color: #f8d7da; color: #721c24; }
    .badge-info { background-color: #d1ecf1; color: #0c5460; }
    .farmer-card {
        background-color: #f8f9fa;
        border-left: 5px solid #28a745;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .tip-box {
        background-color: #e8f5e9;
        border: 1px solid #c8e6c9;
        padding: 12px 16px;
        border-radius: 6px;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------
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
    st.session_state.advisory_lang_code = "en-US"
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


def set_coords(lat, lon, zoom=None, hub_name=None):
    """Update active field coordinates and invalidate cached telemetry + satellite data."""
    st.session_state.coords = {"lat": lat, "lon": lon}
    if zoom is not None:
        st.session_state.zoom = zoom
    if hub_name is not None:
        st.session_state.selected_hub_name = hub_name
    st.session_state.telemetry = None
    st.session_state.satellite = None


def get_client():
    """Resolve a Gemini client from Streamlit secrets or the sidebar input."""
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        api_key = None
    if not api_key:
        api_key = st.session_state.get("manual_api_key")
    return build_genai_client(api_key)


# Farmer-friendly interpretation helpers
def interpret_soil_moisture(val):
    if val is None:
        return "Unknown", "badge-info"
    if val < 0.15:
        return "Dry (Moisture Deficit) ⚠️", "badge-alert"
    elif val <= 0.35:
        return "Optimal Field Capacity 🟢", "badge-optimal"
    else:
        return "Saturated / Waterlogged 💧", "badge-warning"


def interpret_soil_temp(val):
    if val is None:
        return "Unknown", "badge-info"
    if val < 15:
        return "Cool (Dormant Microbes) ❄️", "badge-info"
    elif val <= 32:
        return "Ideal Biological Activity 🪱", "badge-optimal"
    else:
        return "Hot Root Zone (Stress Alert) 🔥", "badge-warning"


def interpret_solar(val):
    if val is None:
        return "Unknown", "badge-info"
    if val < 12:
        return "Overcast / Low Photosynthesis ☁️", "badge-info"
    elif val <= 22:
        return "Moderate Sunlight ⛅", "badge-optimal"
    else:
        return "High Solar Radiation ☀️", "badge-warning"


def interpret_root_wetness(val):
    if val is None:
        return "Unknown", "badge-info"
    if val < 0.25:
        return "Dry Deep Roots 🍂", "badge-alert"
    elif val <= 0.60:
        return "Adequate Subsurface Moisture 🌿", "badge-optimal"
    else:
        return "High Water Table 🌊", "badge-warning"


# ===========================================================================
# SIDEBAR — GLOBAL CONTROLS & TRACK CONTEXT
# ===========================================================================
with st.sidebar:
    st.title("🌱 Faslyn")
    st.caption("**BRICS AgriN Regenerative Agricultural Intelligence**")
    st.markdown("*$0 Digital Public Infrastructure for Smallholders*")

    st.markdown("---")
    st.markdown("### 🔑 AI Extension Officer Setup")
    manual_key = st.text_input(
        "Gemini API Key (Free Tier)",
        type="password",
        value=st.session_state.get("manual_api_key", ""),
        help="Get a free key at https://aistudio.google.com/apikey. "
             "Powers multilingual audio, crop planning & disease vision.",
    )
    if manual_key:
        st.session_state.manual_api_key = manual_key

    if not GENAI_AVAILABLE:
        st.error("`google-genai` package not installed.")
    elif get_client() is None:
        st.warning("⚠️ Enter a Gemini API key to activate voice advice, crop engine & disease scans.")
    else:
        st.success("✅ Gemini 2.5 Flash connected")

    st.markdown("---")
    st.markdown("### 🎯 Track 4 Alignment")
    st.caption(
        "**Theme:** BRICS Cooperation & Food Security\n\n"
        "• **Problem:** Smallholders lack access to high-cost IoT & satellite guidance.\n"
        "• **Solution:** Zero-sensor telemetry (Open-Meteo) + NASA POWER Agroclimatology + Gemini multimodal AI.\n"
        "• **Interoperability:** Open schema compatible with India AgriStack, Brazil EMBRAPA & South Africa AgriPortal."
    )

# ===========================================================================
# HEADER & VALUE PROPOSITION
# ===========================================================================
st.markdown("## 🌱 Faslyn — Regenerative Agricultural Intelligence Network")
st.markdown(
    "**Fas**al (Crop) + **Lyn**k (Connection) · *Inspired by the BRICS AgriN Initiative for Smallholder Cooperation*"
)
st.caption(
    "Transforming free satellite data, zero-sensor soil analytics, and climate forecasting "
    "into actionable, spoken regenerative farming guidance for smallholders across BRICS nations."
)

# Fetch telemetry and satellite data lazily if needed
if st.session_state.telemetry is None:
    with st.spinner("Ingesting ground & soil telemetry from Open-Meteo..."):
        st.session_state.telemetry = fetch_soil_telemetry(
            st.session_state.coords["lat"], st.session_state.coords["lon"]
        )

if st.session_state.satellite is None:
    with st.spinner("Ingesting satellite agro-climatology from NASA POWER..."):
        st.session_state.satellite = fetch_satellite_agroclimatology(
            st.session_state.coords["lat"], st.session_state.coords["lon"]
        )

telemetry = st.session_state.telemetry
satellite = st.session_state.satellite

# ===========================================================================
# USER-FRIENDLY STEPPED WORKFLOW VIA TABS
# ===========================================================================
tabs = st.tabs([
    "📍 1. Farm Location & Hub",
    "🛰️ 2. Field Health & Climate",
    "🎙️ 3. Spoken Agro-Advisor",
    "🌾 4. Regenerative Crop Plan",
    "🩺 5. Leaf Doctor (Disease Scan)",
    "🌐 6. BRICS AgriN Network",
])

# ---------------------------------------------------------------------------
# TAB 1: FARM LOCATION & HUB SELECTOR
# ---------------------------------------------------------------------------
with tabs[0]:
    st.subheader("📍 Step 1: Select Your Farm Location")
    st.markdown(
        "Choose a key BRICS agricultural production hub or click directly on the interactive map "
        "to pinpoint your exact plot."
    )

    col_map_ctrl, col_map_view = st.columns([1, 2])

    with col_map_ctrl:
        current_hub = st.session_state.selected_hub_name
        hub_choice = st.radio(
            "Select BRICS Agricultural Region:",
            list(BRICS_HUBS.keys()),
            index=list(BRICS_HUBS.keys()).index(current_hub) if current_hub in BRICS_HUBS else 0,
            key="hub_radio_selector",
        )

        if st.button("📍 Snap to Selected Hub", use_container_width=True, type="primary"):
            hub = BRICS_HUBS[hub_choice]
            set_coords(hub["lat"], hub["lon"], hub["zoom"], hub_choice)
            st.rerun()

        st.markdown("---")
        st.markdown("**📌 Active Plot Coordinates:**")
        st.code(
            f"Latitude:  {st.session_state.coords['lat']:.4f}\n"
            f"Longitude: {st.session_state.coords['lon']:.4f}",
            language="text",
        )
        st.info("💡 You can also click anywhere on the map to pinpoint an exact field.")

    with col_map_view:
        m = folium.Map(
            location=[st.session_state.coords["lat"], st.session_state.coords["lon"]],
            zoom_start=st.session_state.zoom,
            tiles="OpenStreetMap",
            control_scale=True,
        )

        for name, hub_data in BRICS_HUBS.items():
            folium.Marker(
                [hub_data["lat"], hub_data["lon"]],
                popup=name,
                tooltip=name,
                icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
            ).add_to(m)

        folium.Marker(
            [st.session_state.coords["lat"], st.session_state.coords["lon"]],
            popup="📍 Selected Field",
            tooltip="Active Plot (Click map to move)",
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
        ).add_to(m)

        map_state = st_folium(
            m,
            height=400,
            use_container_width=True,
            key="faslyn_map",
            returned_objects=["last_clicked"],
        )

        if map_state and map_state.get("last_clicked"):
            clicked = map_state["last_clicked"]
            new_lat, new_lon = clicked["lat"], clicked["lng"]
            if (
                round(new_lat, 5) != round(st.session_state.coords["lat"], 5)
                or round(new_lon, 5) != round(st.session_state.coords["lon"], 5)
            ):
                set_coords(new_lat, new_lon, hub_name=f"Custom Field ({new_lat:.2f}, {new_lon:.2f})")
                st.rerun()

# ---------------------------------------------------------------------------
# TAB 2: FIELD HEALTH & CLIMATE TELEMETRY
# ---------------------------------------------------------------------------
with tabs[1]:
    st.subheader("🛰️ Step 2: Live Field Health & Agro-Climatology")
    st.caption(
        "Combines zero-sensor ground telemetry (Open-Meteo) with NASA POWER satellite "
        "agro-climatology — completely eliminating the need for expensive physical IoT sensors."
    )

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
            st.session_state.telemetry = None
            st.session_state.satellite = None
            st.rerun()

    with col_info:
        data_status = "📡 Live Satellite & Telemetry Feeds Active"
        if telemetry.get("source") == "fallback" or satellite.get("source") == "fallback":
            data_status = "⚠️ Operating in Offline/Fallback Mode (Demo Resilience Guarantee)"
        st.success(data_status)

    st.markdown("#### 1. Ground & Soil Micro-Climate (Open-Meteo Zero-Sensor)")
    m_badge_text, m_badge_class = interpret_soil_moisture(telemetry.get("soil_moisture"))
    t_badge_text, t_badge_class = interpret_soil_temp(telemetry.get("soil_temp"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Soil Moisture (0-7cm)",
            f"{telemetry['soil_moisture']:.2f} m³/m³" if telemetry.get("soil_moisture") is not None else "N/A",
        )
        st.markdown(f"<div class='metric-badge {m_badge_class}'>{m_badge_text}</div>", unsafe_allow_html=True)
    with col2:
        st.metric(
            "Soil Temperature",
            f"{telemetry['soil_temp']:.1f} °C" if telemetry.get("soil_temp") is not None else "N/A",
        )
        st.markdown(f"<div class='metric-badge {t_badge_class}'>{t_badge_text}</div>", unsafe_allow_html=True)
    with col3:
        st.metric(
            "Air Temperature",
            f"{telemetry['air_temp']:.1f} °C" if telemetry.get("air_temp") is not None else "N/A",
        )
        st.markdown("<div class='metric-badge badge-optimal'>Ambient Temperature</div>", unsafe_allow_html=True)
    with col4:
        st.metric(
            "Wind Speed",
            f"{telemetry['windspeed']:.1f} km/h" if telemetry.get("windspeed") is not None else "N/A",
        )
        st.markdown("<div class='metric-badge badge-info'>Canopy Aeration</div>", unsafe_allow_html=True)

    if telemetry.get("trend"):
        with st.expander("📈 View 24-Hour Soil & Weather Trend (3-Hour Increments)"):
            st.dataframe(telemetry["trend"], use_container_width=True)

    st.markdown("---")
    st.markdown("#### 2. Satellite Agro-Climatology (NASA POWER Agro Community)")
    s_badge_text, s_badge_class = interpret_solar(satellite.get("solar_radiation"))
    r_badge_text, r_badge_class = interpret_root_wetness(satellite.get("root_zone_soil_wetness"))

    scol1, scol2, scol3 = st.columns(3)
    with scol1:
        st.metric(
            "Solar Radiation",
            f"{satellite['solar_radiation']:.1f} MJ/m²/day" if satellite.get("solar_radiation") is not None else "N/A",
        )
        st.markdown(f"<div class='metric-badge {s_badge_class}'>{s_badge_text}</div>", unsafe_allow_html=True)
    with scol2:
        st.metric(
            "Precipitation",
            f"{satellite['precipitation']:.1f} mm/day" if satellite.get("precipitation") is not None else "N/A",
        )
        st.markdown("<div class='metric-badge badge-info'>Rainfall / Moisture</div>", unsafe_allow_html=True)
    with scol3:
        st.metric(
            "Root-Zone Wetness",
            f"{satellite['root_zone_soil_wetness']:.2f} (0–1)" if satellite.get("root_zone_soil_wetness") is not None else "N/A",
        )
        st.markdown(f"<div class='metric-badge {r_badge_class}'>{r_badge_text}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TAB 3: MULTILINGUAL VOICE AGRO-ADVISOR
# ---------------------------------------------------------------------------
with tabs[2]:
    st.subheader("🎙️ Step 3: Multilingual Voice Agro-Advisor")
    st.caption(
        "Designed for field workers and smallholders with diverse literacy levels. "
        "Gemini 2.5 Flash distills real-time satellite & soil data into exactly three warm, "
        "practical, jargon-free sentences spoken in the farmer's native tongue."
    )

    col_lang, col_action = st.columns([1, 2])
    with col_lang:
        lang_choice = st.selectbox(
            "🌐 Choose Farmer's Language:",
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index("Hindi") if "Hindi" in LANGUAGES else 0,
            key="advisor_lang_dropdown",
        )
        generate_btn = st.button("🎙️ Generate Spoken Advisory", type="primary", use_container_width=True)

    with col_action:
        st.markdown(
            "**Why Voice Matters:** Over 60% of marginal farmers in developing regions "
            "depend on oral advisory. Faslyn uses zero-cost browser speech synthesis "
            "so any budget phone or tablet can speak the recommendations aloud without subscription fees."
        )

    if generate_btn:
        client = get_client()
        if client is None:
            st.info("ℹ️ Running in Instant Demo Mode (Add a free Gemini API key in sidebar for live dynamic AI)")
        try:
            with st.spinner("AI extension officer is preparing your advisory..."):
                advisory = generate_advisory(client, telemetry, lang_choice, satellite=satellite)
            if advisory:
                st.session_state.advisory_text = advisory
                st.session_state.advisory_lang_code = LANGUAGES[lang_choice]
                st.session_state.trigger_speech = True
            else:
                st.error("Empty response received. Please try again.")
        except Exception as e:
            st.error(f"Advisory generation failed: {e}")

    if st.session_state.advisory_text:
        st.markdown("---")
        st.markdown(
            f"""
            <div class='farmer-card'>
                <h4>🗣️ Extension Advisory ({lang_choice})</h4>
                <p style='font-size: 1.15rem; line-height: 1.6;'>{st.session_state.advisory_text}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_audio1, col_audio2 = st.columns([1, 4])
        with col_audio1:
            if st.button("🔊 Replay Audio Advice", use_container_width=True):
                st.session_state.trigger_speech = True
                st.rerun()

        if st.session_state.trigger_speech:
            speak_text(st.session_state.advisory_text, st.session_state.advisory_lang_code)
            st.session_state.trigger_speech = False

# ---------------------------------------------------------------------------
# TAB 4: REGENERATIVE CROP & SOIL PLANNER
# ---------------------------------------------------------------------------
with tabs[3]:
    st.subheader("🌾 Step 4: Regenerative Crop & Soil Recommendation Engine")
    st.caption(
        "Replaces destructive chemical monoculture with regenerative practices: companion "
        "crop rotation, organic soil nourishment, and climate-adaptive water scheduling."
    )

    if st.button("🌾 Generate Regenerative Crop Plan", type="primary"):
        client = get_client()
        if client is None:
            st.info("ℹ️ Running in Instant Demo Mode (Add a free Gemini API key in sidebar for live dynamic AI)")
        try:
            with st.spinner("Analyzing soil biology and agro-climatic conditions..."):
                rec = generate_crop_recommendation(
                    client, telemetry, satellite, st.session_state.get("advisor_lang_dropdown", "English")
                )
            st.session_state.crop_recommendation = rec
        except Exception as e:
            st.error(f"Recommendation generation failed: {e}")

    rec = st.session_state.crop_recommendation
    if rec:
        if "error" in rec:
            st.error(rec["error"])
            if "raw" in rec:
                st.code(rec["raw"])
        else:
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown(
                    f"""
                    <div class='farmer-card' style='border-left-color: #2e7d32;'>
                        <h4>🌱 Recommended Primary Crop</h4>
                        <h2 style='color: #2e7d32; margin: 0;'>{rec.get('recommended_crop', 'N/A')}</h2>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_r2:
                st.markdown(
                    f"""
                    <div class='farmer-card' style='border-left-color: #1976d2;'>
                        <h4>🔁 Companion / Nitrogen-Fixing Rotation</h4>
                        <h2 style='color: #1976d2; margin: 0;'>{rec.get('rotation_partner', 'N/A')}</h2>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            col_r3, col_r4 = st.columns(2)
            with col_r3:
                st.markdown("**🧪 Organic Soil Amendment**")
                st.info(rec.get("soil_amendment", "N/A"))
            with col_r4:
                st.markdown("**💧 Smart Irrigation Guidance**")
                st.info(rec.get("irrigation_guidance", "N/A"))

            st.markdown(
                f"""
                <div class='tip-box'>
                    <strong>Agronomic Rationale:</strong> {rec.get('rationale', 'N/A')}
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# TAB 5: LEAF DOCTOR (DISEASE DIAGNOSTIC SCAN)
# ---------------------------------------------------------------------------
with tabs[4]:
    st.subheader("🩺 Step 5: Visual Plant Disease Diagnostic Scan (Leaf Doctor)")
    st.caption(
        "Multimodal AI diagnosis that identifies plant pathogens, deficiencies, and pests "
        "from a leaf photograph, recommending 100% organic, chemical-free mitigations."
    )

    st.markdown("##### 🧪 Quick Test: Select a Sample Leaf or Upload Your Own")
    sample_col1, sample_col2, sample_col3, sample_col4 = st.columns(4)

    with sample_col1:
        if st.button("🍅 Tomato Early Blight", use_container_width=True):
            if os.path.exists("frontend/samples/tomato_early_blight.png"):
                st.session_state.active_leaf_image = Image.open("frontend/samples/tomato_early_blight.png")
                st.session_state.sample_label = "Sample: Tomato Early Blight (Alternaria solani)"
                st.session_state.diagnosis_text = None

    with sample_col2:
        if st.button("🌾 Rice Blast / Spot", use_container_width=True):
            if os.path.exists("frontend/samples/rice_blast.png"):
                st.session_state.active_leaf_image = Image.open("frontend/samples/rice_blast.png")
                st.session_state.sample_label = "Sample: Rice Blast (Magnaporthe oryzae)"
                st.session_state.diagnosis_text = None

    with sample_col3:
        if st.button("🌽 Healthy Maize Leaf", use_container_width=True):
            if os.path.exists("frontend/samples/healthy_maize.png"):
                st.session_state.active_leaf_image = Image.open("frontend/samples/healthy_maize.png")
                st.session_state.sample_label = "Sample: Healthy Maize Canopy"
                st.session_state.diagnosis_text = None

    with sample_col4:
        if st.button("🔄 Clear Active Image", use_container_width=True):
            st.session_state.active_leaf_image = None
            st.session_state.sample_label = None
            st.session_state.diagnosis_text = None
            st.rerun()

    uploaded_file = st.file_uploader(
        "Or upload a leaf / crop image from your camera or gallery:",
        type=["jpg", "jpeg", "png"],
        key="leaf_uploader_widget",
    )

    if uploaded_file is not None:
        st.session_state.active_leaf_image = Image.open(uploaded_file)
        st.session_state.sample_label = "User Uploaded Image"

    if st.session_state.active_leaf_image is not None:
        col_img, col_diag = st.columns([1, 2])
        with col_img:
            st.image(
                st.session_state.active_leaf_image,
                caption=st.session_state.sample_label or "Selected Leaf Sample",
                use_container_width=True,
            )
            run_diag_btn = st.button("🔍 Run Disease Diagnostic Scan", type="primary", use_container_width=True)

        with col_diag:
            if run_diag_btn:
                client = get_client()
                if client is None:
                    st.info("ℹ️ Running in Instant Demo Mode (Add a free Gemini API key in sidebar for live dynamic AI)")
                try:
                    with st.spinner("Analyzing foliar patterns and pathology..."):
                        diag = generate_diagnosis(
                            client,
                            st.session_state.active_leaf_image,
                            sample_hint=st.session_state.sample_label,
                        )
                    st.session_state.diagnosis_text = diag
                except Exception as e:
                    st.error(f"Diagnostic scan failed: {e}")

            if st.session_state.diagnosis_text:
                st.markdown("#### 📋 Diagnostic Report & Organic Remedy")
                st.info(st.session_state.diagnosis_text)
    else:
        st.info("👆 Click one of the 3 quick-test buttons above or upload an image to test the diagnostic engine.")

# ---------------------------------------------------------------------------
# TAB 6: BRICS AGRIN NETWORK (DIGITAL PUBLIC GOOD)
# ---------------------------------------------------------------------------
with tabs[5]:
    st.subheader("🌐 Step 6: BRICS AgriN Interoperability Network")
    st.caption(
        "Standardized Digital Public Good (DPG) schema — enabling seamless cross-border "
        "collaboration between India, Brazil, South Africa, Russia, China, and partner states."
    )

    interop_schema = {
        "endpoint": "/api/v1/faslyn/export",
        "method": "GET",
        "schema_version": "1.1.0",
        "node": {
            "node_id": "faslyn-demo-node-001",
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
            "sensor_type": "zero-sensor / weather-model reanalysis (Open-Meteo)",
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
            "language": st.session_state.get("advisor_lang_dropdown", "English"),
            "text": st.session_state.advisory_text,
            "model": "gemini-2.5-flash",
        },
        "crop_recommendation": st.session_state.crop_recommendation,
        "diagnostic": {
            "report": st.session_state.diagnosis_text,
            "model": "gemini-2.5-flash (multimodal)",
        },
        "interoperability": {
            "compatible_national_stacks": [
                "🇮🇳 India AgriStack / Kisan e-Mitra",
                "🇧🇷 Brazil Agro API (EMBRAPA-aligned)",
                "🇿🇦 South Africa AgriPortal",
                "🇷🇺 Russia Unified Agro-Informational System",
                "🇨🇳 China National Agricultural Information Network",
            ],
            "data_license": "Open Data Commons Open Database License (ODbL)",
            "sync_protocol": "REST/JSON, offline-first sync queue for low-connectivity fields",
            "cost_model": "$0 — 100% free-tier public infrastructure",
        },
    }

    c_net1, c_net2 = st.columns(2)
    with c_net1:
        st.markdown(
            """
            <div class='farmer-card'>
                <h4>🤝 BRICS Data Solidarity</h4>
                <p>By conforming to an open schema, agricultural research institutes (e.g. ICAR in India, EMBRAPA in Brazil, ARC in South Africa) can share climate-adaptation algorithms without proprietary lock-in.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_net2:
        st.markdown(
            """
            <div class='farmer-card' style='border-left-color: #007bff;'>
                <h4>📦 Digital Public Good (DPG)</h4>
                <p>Zero software licensing fees, zero proprietary sensor vendor lock-in, and full offline-first resilience for remote villages.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("🔍 View Complete Standardized JSON Export Contract", expanded=False):
        st.json(interop_schema)

    st.download_button(
        "⬇️ Download Node Export Contract (JSON)",
        data=json.dumps(interop_schema, indent=2),
        file_name="brics_agrin_node_export.json",
        mime="application/json",
        type="primary",
    )

st.markdown("---")
st.caption("🌱 **Faslyn** — Zero-Cost Regenerative Agricultural Intelligence for BRICS Smallholder Farmers.")
