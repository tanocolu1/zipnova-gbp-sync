from .config import settings

def build_zipnova_payload_from_invoice(inv: dict) -> dict:
    """
    inv: dict normalizado desde GBP (ver main.py normalize_invoice()).
    Reglas:
      - datos de entrega: lo cargado en GBP
      - bulto genérico
      - valor declarado: total sin impuestos
    """

    declared_value = float(inv["total_without_taxes"])

    item_desc = inv.get("item_description") or "Mercadería"
    qty = int(inv.get("items_qty") or 1)

    payload = {
        "account_id": settings.ZIPNOVA_ACCOUNT_ID,
        "origin_id": settings.ZIPNOVA_ORIGIN_ID,
        "source": "GBP",
        "external_id": f"GBP-INV-{inv['invoice_id']}",
        "declared_value": declared_value,

        # si vos querés forzarlo:
        # "logistic_type": "carrier_dropoff",
        # "service_type": "standard_delivery",

        "destination": {
            "name": inv["customer_name"],
            "street": inv["street"],
            "street_number": inv["street_number"],
            "street_extras": inv.get("street_extras", ""),
        },
        "items": [{
            "sku": inv.get("sku") or "GEN",
            "quantity": qty,
            "weight": settings.GENERIC_WEIGHT_KG,
            "height": settings.GENERIC_HEIGHT_CM,
            "width": settings.GENERIC_WIDTH_CM,
            "length": settings.GENERIC_LENGTH_CM,
            "description": item_desc
        }]
    }
    return payload
    