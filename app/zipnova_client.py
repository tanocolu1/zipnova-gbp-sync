import requests
from .config import settings

class ZipnovaClient:
    def __init__(self):
        self.base = settings.ZIPNOVA_BASE_URL.rstrip("/")

    def create_shipment(self, payload: dict) -> dict:
        url = f"{self.base}/shipments"
        r = requests.post(
            url,
            json=payload,
            auth=(settings.ZIPNOVA_USER, settings.ZIPNOVA_PASS),
            headers={"Accept": "application/json"},
            timeout=30
        )
        r.raise_for_status()
        return r.json()
        