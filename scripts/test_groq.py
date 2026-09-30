"""
Test script for live Groq API (Text + Vision).
Usage:
    .\\venv\\Scripts\\python.exe scripts/test_groq.py
"""
import os
import sys
import time
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

# Simple .env parser to avoid requiring external libraries
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k not in os.environ and v:
                os.environ[k] = v

from backend.ai_service import build_grok_client, generate_advisory, generate_diagnosis, generate_crop_recommendation

print("=" * 60)
print("             FASLYN LIVE GROQ API TEST SUITE")
print("=" * 60)

api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("XAI_API_KEY")

if not api_key or "your_" in api_key or len(api_key) < 15:
    print("\n❌ No valid API key found in .env!")
    print("👉 Please open .env and set your key on line 7:")
    print("   GROQ_API_KEY=gsk_your_actual_key_here\n")
    sys.exit(1)

client = build_grok_client(api_key)

print(f"\n🔑 Key detected: {api_key[:8]}...{api_key[-4:]}")
print(f"📡 Provider:     {client.get('provider')}")
print(f"🌐 Base URL:     {client.get('base_url')}")
print(f"🧠 Text Model:   {client.get('text_model')}")
print(f"👁️ Vision Model: {client.get('vision_model')}")
print("-" * 60)

# 1. Test Text Advisory
print("\n[1/3] Testing Live Text Chat (Agro-Advisory)...")
sample_telemetry = {
    "soil_moisture": 0.22,
    "soil_temp": 28.5,
    "air_temp": 32.0,
    "windspeed": 14.2
}
t0 = time.time()
try:
    advisory = generate_advisory(client, sample_telemetry, "English")
    latency = time.time() - t0
    print(f"  ✅ SUCCESS ({latency:.2f}s latency):")
    print(f'  "{advisory}"\n')
except Exception as e:
    print(f"  ❌ FAILED: {e}\n")

# 2. Test Structured JSON Crop Recommendation
print("[2/3] Testing Structured JSON Crop Recommendation Engine...")
sample_satellite = {
    "solar_radiation": 21.5,
    "precipitation": 0.0,
    "root_zone_soil_wetness": 0.28
}
t0 = time.time()
try:
    crop_rec = generate_crop_recommendation(client, sample_telemetry, sample_satellite, "English")
    latency = time.time() - t0
    print(f"  ✅ SUCCESS ({latency:.2f}s latency):")
    print(f"  - Recommended Crop:   {crop_rec.get('recommended_crop')}")
    print(f"  - Rotation Partner:   {crop_rec.get('rotation_partner')}")
    print(f"  - Soil Amendment:     {crop_rec.get('soil_amendment')}")
    print(f"  - Rationale:          {crop_rec.get('rationale')}\n")
except Exception as e:
    print(f"  ❌ FAILED: {e}\n")

# 3. Test Multimodal Vision
print("[3/3] Testing Multimodal Vision (Leaf Disease Pathology)...")
sample_image_path = Path(__file__).parent.parent / "frontend" / "samples" / "tomato_early_blight.png"
if sample_image_path.exists():
    img = Image.open(sample_image_path)
    t0 = time.time()
    try:
        diagnosis = generate_diagnosis(client, img, sample_hint=None)
        latency = time.time() - t0
        print(f"  ✅ SUCCESS ({latency:.2f}s latency):")
        for line in diagnosis.strip().splitlines():
            print(f"    {line}")
        print()
    except Exception as e:
        print(f"  ❌ FAILED: {e}\n")
else:
    print("  ⚠️ Sample image not found, skipping vision test.\n")

print("=" * 60)
print("🎉 ALL GROQ LIVE TESTS COMPLETED!")
print("=" * 60)
