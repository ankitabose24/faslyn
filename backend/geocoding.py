"""
Geocoding service for Faslyn.
Uses OpenStreetMap Nominatim API with fallback resilience and clean naming.
"""
import json
import urllib.parse
import urllib.request
from typing import Optional, Dict, Any


def geocode_location(query: str, timeout: int = 6) -> Optional[Dict[str, Any]]:
    """
    Search for a location query and return coordinates and display info.
    Returns:
        {
            "lat": float,
            "lon": float,
            "display_name": str,
            "short_name": str,
        } or None if not found / error.
    """
    if not query or not query.strip():
        return None

    clean_query = query.strip()
    encoded = urllib.parse.quote(clean_query)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1&addressdetails=1"
    headers = {
        "User-Agent": "Faslyn-RegenerativeAgri/1.0 (agri-intelligence@faslyn.io)"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data and len(data) > 0:
                    first = data[0]
                    lat = float(first["lat"])
                    lon = float(first["lon"])
                    display_name = first.get("display_name", clean_query)

                    # Extract a short clean name (e.g. city, town, village, or state)
                    address = first.get("address", {})
                    short_name = (
                        address.get("city")
                        or address.get("town")
                        or address.get("village")
                        or address.get("county")
                        or address.get("state")
                        or clean_query
                    )

                    return {
                        "lat": lat,
                        "lon": lon,
                        "display_name": display_name,
                        "short_name": short_name,
                    }
    except Exception as e:
        print(f"[Geocoding Warning] Query '{clean_query}' failed: {e}")
        return None

    return None
