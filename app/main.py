from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from .config import settings
from .gbp_client import GBPClient
from .zipnova_client import ZipnovaClient
from .mapper import build_zipnova_payload_from_invoice

app = FastAPI(title="GBP → Zipnova Sync", version="1.0.0")

gbp = GBPClient()  # ahora ya no rompe porque no carga WSDL en __init__
zipnova = ZipnovaClient()
scheduler = BackgroundScheduler()

def normalize_invoice(raw: dict) -> dict:
    """
    Convertí acá la respuesta del WS al formato esperado por mapper.py
    (en cuanto veamos el WSDL real lo dejamos exacto).
    """
    # EJEMPLO de estructura esperada:
    # raw = {
    #   "InvoiceId": "F0001-00001234",
    #   "Status": "FACTURADO",
    #   "Logistics": "ZIPNOVA",
    #   "ZipnovaShipmentId": None,
    #   "CustomerName": "...",
    #   "Delivery": {"Street": "...", "Number": "...", "Extra": "..."},
    #   "Totals": {"TotalWithoutTaxes": 12345.67},
    # }
    return {
        "invoice_id": raw.get("InvoiceId") or raw.get("invoice_id"),
        "status": raw.get("Status") or raw.get("status"),
        "logistics": raw.get("Logistics") or raw.get("logistics"),
        "zipnova_shipment_id": raw.get("ZipnovaShipmentId") or raw.get("zipnova_shipment_id"),

        "customer_name": raw.get("CustomerName") or raw.get("customer_name") or "Cliente",
        "street": (raw.get("Delivery") or {}).get("Street") or raw.get("street") or "",
        "street_number": (raw.get("Delivery") or {}).get("Number") or raw.get("street_number") or "",
        "street_extras": (raw.get("Delivery") or {}).get("Extra") or raw.get("street_extras") or "",

        "total_without_taxes": ((raw.get("Totals") or {}).get("TotalWithoutTaxes")
                                or raw.get("total_without_taxes") or 0),

        "item_description": raw.get("ItemDescription") or raw.get("item_description") or "Mercadería",
        "items_qty": raw.get("ItemsQty") or raw.get("items_qty") or 1,
        "sku": raw.get("SKU") or raw.get("sku") or None,
    }

def should_process(inv: dict) -> bool:
    if inv.get("zipnova_shipment_id"):
        return False

    if settings.GBP_ONLY_FACTURADO and (inv.get("status") or "").upper() != "FACTURADO":
        return False

    if (inv.get("logistics") or "").upper() != settings.GBP_LOGISTICS_ZIPNOVA_VALUE.upper():
        return False

    # validar delivery
    if not inv.get("street") or not inv.get("street_number"):
        return False

    return True

def sync_once() -> dict:
    token = gbp.login_token()

    candidates = gbp.list_invoices_ready_for_zipnova(token)
    results = {"processed": 0, "skipped": 0, "errors": 0, "details": []}

    for c in candidates:
        try:
            # Traer detalle completo
            detail_raw = gbp.get_invoice_detail(token, c.get("invoice_id") or c.get("InvoiceId") or c)
            inv = normalize_invoice(detail_raw)

            if not should_process(inv):
                results["skipped"] += 1
                continue

            payload = build_zipnova_payload_from_invoice(inv)
            z = zipnova.create_shipment(payload)

            shipment_id = str(z.get("id") or z.get("shipment_id") or "")
            tracking = z.get("tracking") or z.get("tracking_number") or ""

            if not shipment_id:
                raise RuntimeError(f"Zipnova response sin shipment_id: {z}")

            gbp.update_invoice_with_zipnova(token, inv["invoice_id"], shipment_id, tracking)

            results["processed"] += 1
            results["details"].append({
                "invoice_id": inv["invoice_id"],
                "shipment_id": shipment_id,
                "tracking": tracking
            })

        except Exception as e:
            results["errors"] += 1
            results["details"].append({"error": str(e)})

    return results

@app.get("/health")
def health():
    return {"ok": True}

import requests
from .config import settings

@app.get("/diag/wsdl")
def diag_wsdl():
    try:
        r = requests.get(settings.GBP_WSDL_URL, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; GBPZipnovaSync/1.0)",
            "Accept": "text/xml,application/xml,*/*"
        })
        return {
            "url": settings.GBP_WSDL_URL,
            "status": r.status_code,
            "content_type": r.headers.get("content-type"),
            "head": r.text[:500]
        }
    except Exception as e:
        return {"url": settings.GBP_WSDL_URL, "error": str(e)}

@app.post("/sync")
def sync():
    """
    Ejecuta sincronización manual.
    """
    return sync_once()

@app.on_event("startup")
def on_startup():
    if settings.SYNC_ENABLED:
        scheduler.add_job(sync_once, "interval", seconds=settings.SYNC_INTERVAL_SECONDS, max_instances=1)
        scheduler.start()
        