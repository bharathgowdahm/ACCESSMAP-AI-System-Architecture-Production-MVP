"""Nominatim Geocoding Client with safety limits."""
import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "AccessMapAI-OpenSourceAccessibilityEngine/1.0"}
_last_request_time = 0.0


def geocode_location(query: str) -> tuple[float, float, str] | None:
    """Geocodes a search string to (latitude, longitude, display_name).
    
    Enforces a 1.0-second rate-limit spacing to comply with OSM Usage Policy.
    """
    global _last_request_time
    if not query or len(query.strip()) < 2:
        return None

    elapsed = time.time() - _last_request_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    try:
        params = {"q": query, "format": "json", "limit": 1}
        resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=5)
        _last_request_time = time.time()
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                name = data[0]["display_name"]
                return lat, lon, name
    except Exception:
        pass
    return None
