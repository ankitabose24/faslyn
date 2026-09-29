"""
Faslyn Interoperable Agricultural REST API Service
==================================================
Standardized machine-to-machine HTTP REST API server implementing the BRICS AgriN
Open Data Protocol and Open Database License (ODbL v1.0).

Built with Python's standard library ThreadingHTTPServer — zero installation,
zero cost, and 100% compliant with digital public goods standards.

Endpoints:
  - GET /                       : API Root, documentation, and metadata
  - GET /api/v1/health          : Service health check
  - GET /api/v1/export          : Complete ODbL DPG interoperability payload
  - GET /api/v1/telemetry       : Live Open-Meteo soil & weather telemetry
  - GET /api/v1/satellite       : Live NASA POWER satellite agroclimatology
  - GET /api/v1/soil            : Live SoilGrids / ISRIC chemical soil profile
  - GET /api/v1/hubs            : BRICS regional agricultural hub registry
"""

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import BRICS_HUBS, FIRST_HUB, REGIONAL_FIELDS
from backend.satellite_service import fetch_satellite_agroclimatology
from backend.soil_service import fetch_soil_profile
from backend.telemetry_service import fetch_soil_telemetry

API_VERSION = "2.0.0"
API_PORT = int(os.environ.get("FASLYN_API_PORT", 8000))


class FaslynApiHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler providing REST endpoints for agricultural interoperability."""

    def _send_json(self, status_code: int, data: dict):
        try:
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("X-Digital-Public-Good", "ODbL-1.0")
            self.send_header("X-Network", "BRICS-AgriN-Cooperation")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        """Handle GET endpoints."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)

        # Default coordinates to India hub if not provided in query string
        try:
            lat = float(query.get("lat", [FIRST_HUB["lat"]])[0])
            lon = float(query.get("lon", [FIRST_HUB["lon"]])[0])
        except (ValueError, TypeError):
            lat = FIRST_HUB["lat"]
            lon = FIRST_HUB["lon"]

        hub_name = query.get("hub", ["India — Odisha (Coastal Rice Belt)"])[0]

        # 1. API Root / Documentation
        if path == "" or path == "/api" or path == "/api/v1":
            doc = {
                "service": "Faslyn BRICS AgriN Interoperable REST API",
                "version": API_VERSION,
                "protocol": "ODbL 1.0 Open Agricultural Public Good",
                "endpoints": {
                    "GET /api/v1/health": "Health and service readiness check",
                    "GET /api/v1/export?lat={lat}&lon={lon}": "Full ODbL DPG interoperable agricultural export",
                    "GET /api/v1/telemetry?lat={lat}&lon={lon}": "Live Open-Meteo zero-sensor soil & weather telemetry",
                    "GET /api/v1/satellite?lat={lat}&lon={lon}": "Live NASA POWER agroclimatology",
                    "GET /api/v1/soil?lat={lat}&lon={lon}": "Live ISRIC SoilGrids chemical soil nutrient profile",
                    "GET /api/v1/hubs": "BRICS regional hubs registry",
                },
                "license": "Open Data Commons Open Database License (ODbL v1.0)",
                "governance": "BRICS Agricultural Information Network (AgriN)",
            }
            self._send_json(200, doc)
            return

        # 2. Health check
        if path == "/api/v1/health":
            self._send_json(200, {
                "status": "healthy",
                "timestamp": "active",
                "service": "faslyn-agrin-api",
                "version": API_VERSION,
            })
            return

        # 3. Telemetry endpoint
        if path == "/api/v1/telemetry":
            data = fetch_soil_telemetry(lat, lon)
            self._send_json(200, {
                "coordinates": {"latitude": lat, "longitude": lon},
                "telemetry": data,
            })
            return

        # 4. Satellite endpoint
        if path == "/api/v1/satellite":
            data = fetch_satellite_agroclimatology(lat, lon)
            self._send_json(200, {
                "coordinates": {"latitude": lat, "longitude": lon},
                "satellite_agroclimatology": data,
            })
            return

        # 5. Soil nutrient profile endpoint
        if path == "/api/v1/soil":
            data = fetch_soil_profile(lat, lon, hub_name)
            self._send_json(200, {
                "coordinates": {"latitude": lat, "longitude": lon},
                "soil_profile": data,
            })
            return

        # 6. Hubs registry endpoint
        if path == "/api/v1/hubs":
            self._send_json(200, {
                "hubs": BRICS_HUBS,
                "regional_fields": REGIONAL_FIELDS,
            })
            return

        # 7. Complete DPG Export endpoint (Main Interoperability Payload)
        if path == "/api/v1/export":
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                f_tel = executor.submit(fetch_soil_telemetry, lat, lon)
                f_sat = executor.submit(fetch_satellite_agroclimatology, lat, lon)
                f_soil = executor.submit(fetch_soil_profile, lat, lon, hub_name)

                telemetry = f_tel.result()
                satellite = f_sat.result()
                soil = f_soil.result()

            export_payload = {
                "schema_version": API_VERSION,
                "node": {
                    "node_id": "faslyn-brics-node-001",
                    "network": "BRICS-AgriN-Cooperation",
                    "operator_type": "smallholder-cooperative",
                },
                "coordinates": {"latitude": lat, "longitude": lon},
                "hub_region": hub_name,
                "ground_telemetry": telemetry,
                "satellite_agroclimatology": satellite,
                "soil_chemical_profile": soil,
                "interoperability": {
                    "compatible_national_stacks": [
                        "🇮🇳 India AgriStack / Kisan e-Mitra",
                        "🇧🇷 Brazil Agro API (EMBRAPA-aligned)",
                        "🇿🇦 South Africa AgriPortal",
                        "🇷🇺 Russia Unified Agro-Informational System",
                        "🇨🇳 China National Agricultural Information Network",
                    ],
                    "data_license": "Open Data Commons Open Database License (ODbL v1.0)",
                    "cost_tier": "100% Free Public Infrastructure (Zero Sensor Cost)",
                },
            }
            self._send_json(200, export_payload)
            return

        # 404 for unknown endpoints
        self._send_json(404, {"error": "Not Found", "requested_path": path})

    def log_message(self, format, *args):
        """Suppress default console logging clutter during app usage."""
        pass


def run_api_server(port: int = API_PORT):
    """Run the API server synchronously."""
    server = ThreadingHTTPServer(("0.0.0.0", port), FaslynApiHandler)
    server.serve_forever()


_SERVER_INSTANCE = None
_SERVER_THREAD = None


def start_api_server_background(port: int = API_PORT) -> bool:
    """Start the API server in a background daemon thread if not already running."""
    global _SERVER_INSTANCE, _SERVER_THREAD
    if _SERVER_INSTANCE is not None:
        return True

    try:
        _SERVER_INSTANCE = ThreadingHTTPServer(("0.0.0.0", port), FaslynApiHandler)
        _SERVER_THREAD = threading.Thread(target=_SERVER_INSTANCE.serve_forever, daemon=True)
        _SERVER_THREAD.start()
        return True
    except OSError:
        # Port already bound (e.g. running from external process)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else API_PORT
    print(f"Starting Faslyn Interoperable REST API on http://0.0.0.0:{port}...")
    run_api_server(port)
