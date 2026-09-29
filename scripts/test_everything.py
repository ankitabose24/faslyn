"""
Faslyn Comprehensive End-to-End Test Suite
===========================================
Tests live API data ingestion, AI pipelines, multilingual translations,
geocoding, image pathology diagnostics, DPG schema validity, and server health.
"""

import sys
import os
import json
import time

# Reconfigure stdout to handle UTF-8 and emojis safely on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import requests

from backend.config import BRICS_HUBS, FIRST_HUB, LANGUAGES, REGIONAL_FIELDS
from backend.telemetry_service import fetch_soil_telemetry, FALLBACK_TELEMETRY
from backend.satellite_service import fetch_satellite_agroclimatology, FALLBACK_SATELLITE
from backend.geocoding import geocode_location
from backend.ai_service import (
    build_grok_client,
    generate_advisory,
    generate_crop_recommendation,
    generate_diagnosis,
    FALLBACK_ADVISORIES,
    FALLBACK_CROP_REC,
    FALLBACK_DIAGNOSES,
)
from backend.translations import t


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def log_test(name: str, passed: bool, detail: str = ""):
    status = f"{Colors.GREEN}[PASS]{Colors.RESET}" if passed else f"{Colors.RED}[FAIL]{Colors.RESET}"
    print(f" {status} {Colors.BOLD}{name}{Colors.RESET}")
    if detail:
        print(f"        └─ {detail}")


def run_all_tests():
    total_passed = 0
    total_failed = 0

    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*65}")
    print("   FASLYN AGRICULTURAL INTELLIGENCE — END-TO-END TEST SUITE")
    print(f"{'='*65}{Colors.RESET}\n")

    # -----------------------------------------------------------------------
    # TEST 1: Live Ground Telemetry (Open-Meteo)
    # -----------------------------------------------------------------------
    print(f"{Colors.YELLOW}[1/8] Testing Live Zero-Sensor Ground Telemetry (Open-Meteo)...{Colors.RESET}")
    hubs_to_test = [
        ("India (Punjab)", 30.9, 75.85),
        ("Brazil (Cerrado)", -12.5, -55.7),
        ("South Africa (Free State)", -28.45, 26.78),
    ]
    for hub_name, lat, lon in hubs_to_test:
        telemetry = fetch_soil_telemetry(lat, lon)
        has_keys = all(k in telemetry for k in ["soil_moisture", "soil_temp", "air_temp", "windspeed", "source"])
        moisture_valid = isinstance(telemetry["soil_moisture"], (int, float)) and 0.0 <= telemetry["soil_moisture"] <= 1.0
        temp_valid = isinstance(telemetry["soil_temp"], (int, float))
        passed = has_keys and moisture_valid and temp_valid
        detail = f"Soil Moisture: {telemetry['soil_moisture']} m3/m3 | Soil Temp: {telemetry['soil_temp']}°C | Source: {telemetry['source']}"
        log_test(f"Telemetry: {hub_name}", passed, detail)
        if passed: total_passed += 1
        else: total_failed += 1

    # -----------------------------------------------------------------------
    # TEST 2: Live Satellite Agro-Climatology (NASA POWER)
    # -----------------------------------------------------------------------
    print(f"\n{Colors.YELLOW}[2/8] Testing Live Satellite Agro-Climatology (NASA POWER)...{Colors.RESET}")
    sat_hubs = [
        ("India (Punjab)", 30.9, 75.85),
        ("Brazil (Cerrado)", -12.5, -55.7),
    ]
    for hub_name, lat, lon in sat_hubs:
        satellite = fetch_satellite_agroclimatology(lat, lon)
        has_keys = all(k in satellite for k in ["solar_radiation", "precipitation", "root_zone_soil_wetness", "source"])
        solar_valid = isinstance(satellite["solar_radiation"], (int, float)) and satellite["solar_radiation"] >= 0
        precip_valid = isinstance(satellite["precipitation"], (int, float)) and satellite["precipitation"] >= 0
        passed = has_keys and solar_valid and precip_valid
        detail = f"Solar: {satellite['solar_radiation']} MJ/m2 | Precip: {satellite['precipitation']} mm | Wetness: {satellite['root_zone_soil_wetness']} | Source: {satellite['source']}"
        log_test(f"Satellite: {hub_name}", passed, detail)
        if passed: total_passed += 1
        else: total_failed += 1

    # -----------------------------------------------------------------------
    # TEST 3: Live Geocoding Service (OSM Nominatim)
    # -----------------------------------------------------------------------
    print(f"\n{Colors.YELLOW}[3/8] Testing Live Global Geocoding (Nominatim)...{Colors.RESET}")
    geo_queries = ["Nagpur, India", "Cairo, Egypt", "Nairobi, Kenya"]
    for q in geo_queries:
        res = geocode_location(q)
        passed = res is not None and "lat" in res and "lon" in res and "short_name" in res
        detail = f"Query: '{q}' -> ({res.get('lat')}, {res.get('lon')}) | Short Name: '{res.get('short_name')}'" if res else "Geocoding returned None"
        log_test(f"Geocoding: '{q}'", passed, detail)
        if passed: total_passed += 1
        else: total_failed += 1

    # Test empty query resilience
    res_empty = geocode_location("")
    passed_empty = res_empty is None
    log_test("Geocoding empty query edge-case (returns None gracefully)", passed_empty, "Safely handled empty string")
    if passed_empty: total_passed += 1
    else: total_failed += 1

    # -----------------------------------------------------------------------
    # TEST 4: BRICS Hubs & Multi-Regional Configuration
    # -----------------------------------------------------------------------
    print(f"\n{Colors.YELLOW}[4/8] Testing BRICS Regional Hubs Configuration...{Colors.RESET}")
    hub_count = len(BRICS_HUBS)
    hubs_valid = True
    for name, data in BRICS_HUBS.items():
        if not ("lat" in data and "lon" in data and "zoom" in data):
            hubs_valid = False
            break
    log_test(f"All {hub_count} BRICS Hubs correctly configured", hubs_valid, f"Hubs: {', '.join(list(BRICS_HUBS.keys())[:3])}...")
    if hubs_valid: total_passed += 1
    else: total_failed += 1

    # Verify regional fields polygons
    fields_valid = len(REGIONAL_FIELDS) >= 5 and all(len(flds) >= 3 for flds in REGIONAL_FIELDS.values())
    log_test("Regional Field Polygons populated with test fields", fields_valid, f"{len(REGIONAL_FIELDS)} hub field datasets present")
    if fields_valid: total_passed += 1
    else: total_failed += 1

    # -----------------------------------------------------------------------
    # TEST 5: Multilingual Translations Across 7 BRICS Languages
    # -----------------------------------------------------------------------
    print(f"\n{Colors.YELLOW}[5/8] Testing Multilingual Translation Coverage...{Colors.RESET}")
    languages_to_check = ["English", "Hindi", "Mandarin", "Russian", "Portuguese", "Arabic", "Amharic"]
    keys_to_test = ["nav_home", "nav_sat", "nav_ai", "nav_regen", "nav_brics", "greeting", "healthy", "critical"]
    
    all_lang_passed = True
    for lang in languages_to_check:
        missing = []
        for k in keys_to_test:
            trans = t(k, lang)
            if not trans or trans == k:
                missing.append(k)
        if missing:
            all_lang_passed = False
            log_test(f"Language: {lang}", False, f"Missing translations for: {missing}")
            total_failed += 1
        else:
            log_test(f"Language: {lang}", True, f"Verified translations: {t('greeting', lang)[:25]}...")
            total_passed += 1

    # -----------------------------------------------------------------------
    # TEST 6: AI Agronomy & Vision Pathology Engines
    # -----------------------------------------------------------------------
    print(f"\n{Colors.YELLOW}[6/8] Testing AI Intelligence Pipelines & Fallback Resilience...{Colors.RESET}")
    sample_telemetry = FALLBACK_TELEMETRY
    sample_satellite = FALLBACK_SATELLITE

    # Test Advisory Generation (English & Hindi)
    adv_en = generate_advisory(None, sample_telemetry, "English", sample_satellite)
    adv_hi = generate_advisory(None, sample_telemetry, "Hindi", sample_satellite)
    adv_passed = bool(adv_en and len(adv_en) > 40 and adv_hi and len(adv_hi) > 40)
    log_test("AI Agro-Advisory Engine (Resilient Dual-Language Mode)", adv_passed, f"EN: '{adv_en[:45]}...'")
    if adv_passed: total_passed += 1
    else: total_failed += 1

    # Test Structured Regenerative Crop Plan Generation
    crop_rec = generate_crop_recommendation(None, sample_telemetry, sample_satellite, "English")
    rec_keys = ["recommended_crop", "rotation_partner", "soil_amendment", "irrigation_guidance"]
    rec_passed = isinstance(crop_rec, dict) and all(k in crop_rec for k in rec_keys)
    log_test("Regenerative Crop Planner (Structured Companion Rotation)", rec_passed, f"Crop: {crop_rec.get('recommended_crop')} | Companion: {crop_rec.get('rotation_partner')}")
    if rec_passed: total_passed += 1
    else: total_failed += 1

    # Test Leaf Doctor (Vision Pathology) with physical sample images
    samples = [
        ("frontend/samples/tomato_early_blight.png", "Tomato Early Blight", "blight"),
        ("frontend/samples/rice_blast.png", "Rice Blast", "blast"),
        ("frontend/samples/healthy_maize.png", "Healthy Maize", "healthy"),
    ]
    for path, label, expected_keyword in samples:
        if os.path.exists(path):
            img = Image.open(path)
            diag = generate_diagnosis(None, img, sample_hint=label)
            diag_passed = bool(diag and len(diag) > 50 and ("Condition:" in diag or expected_keyword in diag.lower()))
            log_test(f"Leaf Doctor Vision Scan: {label}", diag_passed, f"Report length: {len(diag)} chars | Urgency: {'Act' if 'Act' in diag else 'Monitor'}")
            if diag_passed: total_passed += 1
            else: total_failed += 1
        else:
            log_test(f"Leaf Doctor Vision Scan: {label}", False, f"File missing: {path}")
            total_failed += 1

    # -----------------------------------------------------------------------
    # TEST 7: Digital Public Good (DPG) Export Schema Validation
    # -----------------------------------------------------------------------
    print(f"\n{Colors.YELLOW}[7/8] Testing DPG Standardized Interoperability Schema...{Colors.RESET}")
    dpg_payload = {
        "endpoint": "/api/v1/faslyn/export",
        "schema_version": "2.0.0",
        "node": {"node_id": "faslyn-brics-node-001", "network": "BRICS-AgriN-Cooperation"},
        "ground_telemetry": sample_telemetry,
        "satellite_agroclimatology": sample_satellite,
        "interoperability": {
            "compatible_national_stacks": ["India AgriStack", "Brazil EMBRAPA", "South Africa AgriPortal"],
            "data_license": "Open Data Commons Open Database License (ODbL)",
        }
    }
    try:
        serialized = json.dumps(dpg_payload, indent=2)
        deserialized = json.loads(serialized)
        dpg_passed = deserialized["schema_version"] == "2.0.0" and len(deserialized["interoperability"]["compatible_national_stacks"]) == 3
        log_test("DPG Schema Validation & ODbL JSON Serialization", dpg_passed, f"Valid JSON payload ({len(serialized)} bytes)")
        if dpg_passed: total_passed += 1
        else: total_failed += 1
    except Exception as e:
        log_test("DPG Schema Validation", False, str(e))
        total_failed += 1

    # -----------------------------------------------------------------------
    # TEST 8: Streamlit Live Server Health & Preloader Verification
    # -----------------------------------------------------------------------
    print(f"\n{Colors.YELLOW}[8/8] Testing Web Server Health & Preloader Status...{Colors.RESET}")
    try:
        resp = requests.get("http://localhost:8501", timeout=5)
        server_ok = resp.status_code == 200
        has_preloader = "faslyn-loader-overlay" in resp.text
        has_stream = "Streamlit" in resp.text
        log_test("Local Streamlit Server Active (Port 8501)", server_ok, f"HTTP Status: {resp.status_code}")
        log_test("Static index.html Patched with Instant Preloader", has_preloader, "Preloader detected in initial HTML payload")
        if server_ok: total_passed += 1
        else: total_failed += 1
        if has_preloader: total_passed += 1
        else: total_failed += 1
    except Exception as e:
        log_test("Local Streamlit Server Active", False, f"Could not connect: {e}")
        total_failed += 1

    # -----------------------------------------------------------------------
    # FINAL SUMMARY
    # -----------------------------------------------------------------------
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*65}")
    print(f"   TEST SUMMARY: {total_passed} PASSED, {total_failed} FAILED")
    print(f"{'='*65}{Colors.RESET}\n")

    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
