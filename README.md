# 🌱 Faslyn — BRICS Regenerative Agricultural Intelligence Network

> **Fas**al (Crop) + **Lyn**k (Connection)  
> *A \$0 Digital Public Infrastructure (DPI) connecting crop data, satellite intelligence, and smallholder farmers across BRICS nations.*

---

## 🏆 Hackathon Track Alignment
* **Track:** Track 4 — AgriN & Regenerative Agricultural Intelligence
* **Theme:** BRICS Cooperation (India · Brazil · South Africa · Russia · China)
* **Digital Public Good (DPG):** Aligned with India's AgriStack, Brazil's EMBRAPA Agro API, and South Africa's AgriPortal.

---

## 📌 Project Overview & The Crisis
Small and marginal farmers across emerging economies produce over 80% of local food supplies, yet:
* **The Hardware Divide:** Commercial precision farming relies on expensive IoT soil sensors (\$300–\$1,000+), lab tests, and commercial subscriptions that marginal farmers cannot afford.
* **Climate Shocks:** Erratic rainfall, severe droughts, and unseasonal heatwaves render traditional generational wisdom obsolete.
* **Information Silos:** Lack of shared digital infrastructure prevents cross-border collaboration on climate-resilient crop and soil practices.

**Faslyn solves this by providing a 100% zero-hardware, satellite-fused, multilingual agricultural intelligence platform at zero cost.**

---

## 🚀 Key Features

1. **📍 BRICS Agricultural Hub Pinpointer:**
   * Pre-configured production belts: Odisha (India), Mato Grosso (Brazil), Limpopo (South Africa), Krasnodar Krai (Russia), Heilongjiang (China).
   * Interactive Folium map with custom GPS plot selection.

2. **🛰️ Dual-Layer Zero-Sensor Ingestion:**
   * **Ground & Soil Telemetry (Open-Meteo):** Real-time hourly 0–7cm soil moisture, topsoil temperature, ambient weather, and 24h trends without physical sensors.
   * **Satellite Agro-Climatology (NASA POWER AG):** Genuine satellite-derived solar radiation ($MJ/m^2/day$), precipitation, and root-zone water balance.

3. **🎙️ Multilingual Spoken AI Extension Officer:**
   * Powered by **Gemini 2.5 Flash**, synthesizing complex data into exactly three warm, encouraging, jargon-free spoken sentences.
   * Native browser Web Speech TTS ($0 cost) supporting **7 BRICS languages**: Hindi, Odia, Portuguese, Russian, Swahili, Mandarin, and English.

4. **🌾 Regenerative Crop & Soil Recommendation Engine:**
   * Replaces chemical monoculture with regenerative practices: climate-matched primary crops, nitrogen-fixing companion rotations, organic amendments (FYM, biochar, vermicompost), and smart irrigation scheduling.

5. **🩺 Leaf Doctor — Multimodal Disease Diagnostic Scan:**
   * AI-powered foliar disease diagnosis from photos or 1-click test samples (Tomato Early Blight, Rice Blast, Healthy Maize).
   * Generates confidence ratings and **100% organic, non-chemical remedies**.

6. **🌐 Cross-Border Interoperability Schema (ODbL):**
   * Standardized open JSON export contract (`/api/v1/faslyn/export`) enabling open data exchange and model sharing among BRICS agricultural research bodies.

---

## 🛠️ Architecture & Tech Stack

```
[ Farm GPS / Hub ] ──▶ [ Open-Meteo API (Ground Telemetry) ]
                   ──▶ [ NASA POWER API (Satellite Agroclimatology) ]
                               │
                               ▼
               [ Multimodal Gemini 2.5 Flash Engine ]
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
[ Spoken Voice Audio ]  [ Regenerative Plan ]  [ Leaf Vision Scan ]
 (Hindi, Odia, etc.)    (Crop, Legume, Soil)   (Organic Mitigation)
                               │
                               ▼
        [ BRICS AgriN Open Interoperability Schema (JSON) ]
```

* **Frontend:** Streamlit, Streamlit-Folium, Web Speech API (Client-side TTS)
* **Backend:** Python 3.11+, Requests, Pillow
* **Data Sources:** Open-Meteo API, NASA POWER Agroclimatology API
* **AI Models:** Google Gemini 2.5 Flash (Text & Multimodal Vision via `google-genai` SDK)
* **Cost Model:** \$0 — completely free tier & open APIs

---

## 💻 Local Setup & Installation

### Prerequisites
* Python 3.10 or higher
* (Optional) Free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/apikey)

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

# 4. Run the application
streamlit run frontend/app.py
```

Open your browser at `http://localhost:8501`.

---

## 📄 License
This project is licensed as an Open Digital Public Good under the **Open Data Commons Open Database License (ODbL)**.
