import math
import json
import os
from typing import List, Dict, Any, Optional, Tuple

STORES_FILE = os.path.join(os.path.dirname(__file__), "../data/stores.json")
SEARCH_RADIUS_KM = 3.0


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two lat/lon points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _load_stores() -> List[Dict[str, Any]]:
    try:
        with open(STORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return _mock_stores()


def _mock_stores() -> List[Dict[str, Any]]:
    """Placeholder stores — replace with real database."""
    return [
        {
            "id": 1,
            "name": "Central Store Bangkok",
            "address": "123 Sukhumvit Rd, Bangkok",
            "region": "Bangkok",
            "hours": "09:00 - 22:00",
            "lat": 13.7367,
            "lon": 100.5601,
            "photo_url": None,
        },
        {
            "id": 2,
            "name": "Phuket Branch",
            "address": "456 Thepkasattri Rd, Phuket",
            "region": "Phuket",
            "hours": "10:00 - 21:00",
            "lat": 7.8804,
            "lon": 98.3923,
            "photo_url": None,
        },
        {
            "id": 3,
            "name": "Moscow Flagship",
            "address": "ул. Тверская, 15, Москва",
            "region": "Moscow",
            "hours": "10:00 - 22:00",
            "lat": 55.7617,
            "lon": 37.6117,
            "photo_url": None,
        },
    ]


def find_stores_by_location(lat: float, lon: float, radius_km: float = SEARCH_RADIUS_KM) -> List[Dict[str, Any]]:
    stores = _load_stores()
    results = []
    for store in stores:
        dist = _haversine(lat, lon, store["lat"], store["lon"])
        if dist <= radius_km:
            results.append({**store, "distance_km": round(dist, 2)})
    results.sort(key=lambda s: s["distance_km"])
    return results[:5]


def find_stores_by_region(region: str) -> List[Dict[str, Any]]:
    stores = _load_stores()
    return [s for s in stores if region.lower() in s.get("region", "").lower()][:5]


def get_all_regions() -> List[str]:
    stores = _load_stores()
    return sorted(set(s.get("region", "") for s in stores if s.get("region")))
