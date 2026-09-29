# 🌱 Faslyn — BRICS Regenerative Agricultural Intelligence Network

> **Fas**al (Crop) + **Lyn**k (Connection)  
> *A $0 Digital Public Infrastructure (DPI) connecting crop telemetry, NASA satellite agro-climatology, and smallholder farmers across BRICS nations.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38%2B-FF4B4B.svg)](https://streamlit.io)
[![NASA POWER](https://img.shields.io/badge/NASA%20POWER-Agroclimatology-orange.svg)](https://power.larc.nasa.gov)
[![Open-Meteo](https://img.shields.io/badge/Open--Meteo-Zero--Sensor%20Soil-green.svg)](https://open-meteo.com)
[![License: ODbL](https://img.shields.io/badge/License-ODbL%201.0-brightgreen.svg)](https://opendatacommons.org/licenses/odbl/)
[![Tests](https://img.shields.io/badge/Tests-26%20Passed-success.svg)](scripts/test_everything.py)

---

## 🏆 Hackathon Track Alignment
* **Track:** Track 4 — AgriN & Regenerative Agricultural Intelligence
* **Theme:** BRICS Cooperation (🇮🇳 India · 🇧🇷 Brazil · 🇿🇦 South Africa · 🇷🇺 Russia · 🇨🇳 China · 🇪🇬 Egypt · 🇪🇹 Ethiopia)
* **Digital Public Good (DPG):** Aligned with India's AgriStack, Brazil's EMBRAPA Agro API, and South Africa's AgriPortal under Open Data Commons (ODbL).

---

## 📌 Project Overview & The Problem
Small and marginal farmers across emerging economies produce over 80% of local food supplies, yet:
* **The Hardware Barrier:** Traditional precision agriculture assumes farmers have expensive IoT soil sensors ($300–$1,000+), lab tests, and recurring subscriptions that smallholders cannot afford.
* **Climate Shocks:** Erratic rainfall, severe droughts, and unseasonal heatwaves render traditional generational wisdom obsolete.
* **Information Silos:** Absence of shared digital infrastructure prevents cross-border collaboration on climate-resilient crop and soil practices.

**Faslyn solves this by providing a 100% zero-hardware, satellite-fused, multilingual agricultural intelligence platform at zero cost.**

---

## 🚀 Key Features

1. **📍 BRICS Regional Hub Pinpointer & Global Geocoding:**
   * Pre-configured production belts across India, Brazil, South Africa, Russia, and China.
   * Interactive Folium map with OpenStreetMap Nominatim live GPS geocoding.

2. **🛰️ Dual-Layer Zero-Sensor Ingestion ($0 Hardware):**
   * **Ground & Soil Telemetry (Open-Meteo):** Real-time hourly 0–7cm volumetric soil moisture, topsoil temperature, ambient weather, and 24h trends without physical sensors.
   * **Satellite Agro-Climatology (NASA POWER AG):** Live satellite-observed solar radiation ($MJ/m^2/day$), precipitation, and root-zone water balance.

3. **🎙️ Multilingual Spoken AI Extension Officer:**
   * Powered by **xAI Grok-2**, synthesizing complex data into exactly three warm, encouraging, jargon-free spoken sentences.
   * Native browser Web Speech TTS ($0 cost) supporting **7 BRICS languages**: Hindi, Odia, Portuguese, Russian, Swahili, Mandarin, and English.

4. **🌾 Regenerative Crop & Soil Recommendation Engine:**
   * Replaces chemical monoculture with regenerative practices: climate-matched primary crops, nitrogen-fixing companion rotations (Cowpea, Pigeon Pea), organic amendments (biochar, FYM, vermicompost), and deficit irrigation scheduling.

5. **🩺 Leaf Doctor — Multimodal Vision Pathology:**
   * AI-powered foliar disease diagnosis from photos or 1-click test samples (Tomato Early Blight, Rice Blast, Healthy Maize).
   * Diagnoses conditions and prescribes **100% organic, low-cost bio-remedies** (neem oil extract, *Trichoderma*, biochar, cultural companion rotation).

6. **🌐 Cross-Border Interoperability Schema (ODbL DPG):**
   * Standardized open JSON export contract (`/api/v1/faslyn/export`) enabling open data exchange among BRICS agricultural research bodies.

7. **⚡ Instant 0ms Preloader & Responsive Touch UI:**
   * Embedded preloader in `index.html` ensuring zero flash of content on page load with smooth 3D zoom-in dashboard entrance.
   * Full mobile & touch support with Apple HIG/Android 48px touch targets.

---

## 🛠️ Architecture & Tech Stack

```
[ Farm GPS / Hub / Search ] ──▶ [ Open-Meteo API (Ground Soil Telemetry) ]
                             ──▶ [ NASA POWER API (Satellite Agroclimatology) ]
                                          │
                                          ▼
                         [ xAI Grok-2 Intelligence Engine ]
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        ▼                                 ▼                                 ▼
[ Spoken Voice Audio ]          [ Regenerative Plan ]             [ Leaf Vision Scan ]
(Hindi, Odia, Portuguese, etc.) (Crop, Legume, Biochar)           (Organic Pathogen Remedy)
                                          │
                                          ▼
                  [ BRICS AgriN Open DPG Schema (ODbL JSON) ]
```

* **Frontend:** Streamlit 1.38+, Streamlit-Folium, Web Speech API (Client-side TTS)
* **Backend:** Python 3.10+, Requests, Pillow
* **Data Feeds:** Open-Meteo API, NASA POWER Agroclimatology API, OSM Nominatim
* **AI Engine:** xAI Grok-2 (Text & Multimodal Vision) with resilient offline demo fallbacks
* **Cost Model:** $0 — 100% free-tier digital public infrastructure

---

## 💻 Local Setup & Installation

### Quick Start
```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/faslyn.git
cd faslyn

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Run the automated test suite
python scripts/test_everything.py

# 5. Launch the application
streamlit run frontend/app.py
```

Open your browser at `http://localhost:8501`.

---

## 🧪 Testing & Verification
Faslyn includes an automated test suite verifying live API connectivity, data bounds, translations, and AI models:
```bash
python scripts/test_everything.py
```
**Results:** `26 Passed, 0 Failed (100% Pass Rate)`.

---

## 📄 License
This project is licensed as an Open Digital Public Good under the **Open Data Commons Open Database License (ODbL 1.0)**.
