from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import base64

from .config import settings
from .gbp_client import GBPClient
from .zipnova_client import ZipnovaClient
from .mapper import build_zipnova_payload_from_invoice

app = FastAPI(title="GBP → Zipnova Sync", version="1.0.0")

gbp = GBPClient()
zipnova = ZipnovaClient()
scheduler = BackgroundScheduler()


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {"ok": True}


# ============================================================
# DIAGNOSTICO WSDL
# ============================================================

@app.get("/diag/wsdl")
def diag_wsdl():
    try:
        r = requests.get(
            settings.GBP_WSDL_URL,
            timeout=20,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; GBPZipnovaSync/1.0)",
                "Accept": "text/xml,application/xml,*/*"
            }
        )

        content = r.content or b""
        head_bytes = content[:400]

        return {
            "requested_url": settings.GBP_WSDL_URL,
            "final_url": r.url,
            "status": r.status_code,
            "history": [{"status": h.status_code, "url": h.url} for h in r.history],
            "content_type": r.headers.get("content-type"),
            "content_length_header": r.headers.get("content-length"),
            "bytes_len": len(content),
            "head_text_preview": head_bytes.decode("utf-8", errors="replace")
        }

    except Exception as e:
        return {
            "requested_url": settings.GBP_WSDL_URL,
            "error": str(e)
        }


# ============================================================
# NORMALIZACION (adaptar cuando tengamos WSDL real)
# ============================================================

def normalize_invoice(raw: dict) -> dict:
    return {
        "invoice_id": raw.get("InvoiceId") or raw.get("invoice_id"),
        "status": raw.get("Status") or raw.get("status"),
        "logistics": raw.get("Logistics") or raw.get("logistics"),
        "zipnova_shipment_id": raw.get("ZipnovaShipmentId") or raw.get("zipnova_shipment_id"),

        "customer_name": raw.get("CustomerName") or raw.get("customer_name") or "Cliente",
        "street": (raw.get("Delivery") or {}).get("Street") or raw.get("street") or "",
        "street_number": (raw.get("Delivery") or {}).get("Number") or raw.get("street_number") or "",
        "street_extras": (raw.get("Delivery") or {}).get("Extra") or raw.get("street_extras") or "",

        "total_without_taxes": (
            (raw.get("Totals") or {}).get("TotalWithoutTaxes")
            or raw.get("total_without_taxes")
            or 0
        ),

        "item_description": raw.get("ItemDescription") or raw.get("item_description") or "Mercadería",
        "items_qty": raw.get("ItemsQty") or raw.get("items_qty") or 1,
        "sku": raw.get("SKU") or raw.get("sku") or None,
    }


# ============================================================
# REGLAS DE NEGOCIO
# ============================================================

def should_process(inv: dict) -> bool:

    if inv.get("zipnova_shipment_id"):
        return False

    if settings.GBP_ONLY_FACTURADO:
        if (inv.get("status") or "").upper() != "FACTURADO":
            return False

    if (inv.get("logistics") or "").upper() != settings.GBP_LOGISTICS_ZIPNOVA_VALUE.upper():
        return False

    if not inv.get("street") or not inv.get("street_number"):
        return False

    return True


# ============================================================
# SINCRONIZACION
# ============================================================

def sync_once() -> dict:

    results = {"processed": 0, "skipped": 0, "errors": 0, "details": []}

    try:
        token = gbp.login_token()
    except NotImplementedError:
        return {"error": "GBP methods not implemented yet"}

    candidates = gbp.list_invoices_ready_for_zipnova(token)

    for c in candidates:
        try:
            detail_raw = gbp.get_invoice_detail(token, c.get("invoice_id") or c)
            inv = normalize_invoice(detail_raw)

            if not should_process(inv):
                results["skipped"] += 1
                continue

            payload = build_zipnova_payload_from_invoice(inv)
            z = zipnova.create_shipment(payload)

            shipment_id = str(z.get("id") or z.get("shipment_id") or "")
            tracking = z.get("tracking") or z.get("tracking_number") or ""

            if not shipment_id:
                raise RuntimeError(f"Zipnova response without shipment_id: {z}")

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


@app.post("/sync")
def sync():
    return sync_once()


# ============================================================
# SCHEDULER
# ============================================================

@app.on_event("startup")
def on_startup():
    if settings.SYNC_ENABLED:
        scheduler.add_job(sync_once, "interval", seconds=settings.SYNC_INTERVAL_SECONDS, max_instances=1)
        scheduler.start()
        