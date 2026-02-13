from zeep import Client
from zeep.transports import Transport
from requests import Session
from .config import settings

class GBPClient:
    def __init__(self):
        session = Session()
        session.verify = True
        transport = Transport(session=session, timeout=30)
        self.client = Client(settings.GBP_WSDL_URL, transport=transport)

    def login_token(self) -> str:
        """
        REEMPLAZAR por el método real del WS.
        Usualmente: Login(user, pass) -> token
        """
        # Ejemplo:
        # resp = self.client.service.Login(settings.GBP_USER, settings.GBP_PASS)
        # return resp.Token if hasattr(resp, "Token") else resp
        raise NotImplementedError("Completar método login_token() con el WSDL real")

    def list_invoices_ready_for_zipnova(self, token: str) -> list[dict]:
        """
        Debe devolver lista de comprobantes facturados cuyo método/logística sea ZIPNOVA
        y que NO tengan zipnova_shipment_id asignado aún.
        Cada item idealmente: { "invoice_id": "...", "logistics": "...", "status": "...", "zipnova_shipment_id": None }
        """
        # Ejemplo:
        # return self.client.service.Facturas_ListarParaEnvio(token)
        raise NotImplementedError("Completar método list_invoices_ready_for_zipnova()")

    def get_invoice_detail(self, token: str, invoice_id: str) -> dict:
        """
        Devuelve el detalle con:
          - delivery_address (calle, número, extra, localidad, provincia, cp)
          - customer_name
          - totals: total_without_taxes
          - items: (opcional) o al menos descripción
          - logistics seleccionado
        """
        # Ejemplo:
        # return self.client.service.Factura_ObtenerDetalle(token, invoice_id)
        raise NotImplementedError("Completar método get_invoice_detail()")

    def update_invoice_with_zipnova(self, token: str, invoice_id: str, shipment_id: str, tracking: str | None) -> None:
        """
        Guarda en GBP el shipment_id/tracking para que quede ligado al comprobante y no se duplique.
        """
        # Ejemplo:
        # self.client.service.Factura_ActualizarCamposEnvio(token, invoice_id, shipment_id, tracking or "")
        raise NotImplementedError("Completar método update_invoice_with_zipnova()")
        