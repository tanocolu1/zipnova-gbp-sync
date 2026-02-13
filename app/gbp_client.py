from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from zeep import Client, Settings as ZeepSettings
from zeep.transports import Transport
from requests import Session
from .config import settings


@dataclass
class GBPClient:
    _client: Optional[Client] = None

    def _get_client(self) -> Client:
        """
        Lazy-load del WSDL: NO se carga en import/startup.
        Esto evita que Railway caiga si el WSDL está bloqueado.
        """
        if self._client is not None:
            return self._client

        session = Session()
        session.verify = True
        # Algunos servidores devuelven 403 si el UA es "python-requests"
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; GBPZipnovaSync/1.0)",
            "Accept": "text/xml,application/xml,*/*",
        })

        transport = Transport(session=session, timeout=30)

        zeep_settings = ZeepSettings(strict=False, xml_huge_tree=True)

        self._client = Client(settings.GBP_WSDL_URL, transport=transport, settings=zeep_settings)
        return self._client

    def login_token(self) -> str:
        client = self._get_client()

        # TODO: reemplazar por el método real según tu WSDL
        # resp = client.service.Login(settings.GBP_USER, settings.GBP_PASS)
        # token = resp.Token if hasattr(resp, "Token") else resp
        raise NotImplementedError("Completar login_token() con el método real del WSDL")

    def list_invoices_ready_for_zipnova(self, token: str) -> list[dict]:
        client = self._get_client()
        # TODO: método real
        raise NotImplementedError("Completar list_invoices_ready_for_zipnova() con el WSDL")

    def get_invoice_detail(self, token: str, invoice_id: str) -> dict:
        client = self._get_client()
        # TODO: método real
        raise NotImplementedError("Completar get_invoice_detail() con el WSDL")

    def update_invoice_with_zipnova(self, token: str, invoice_id: str, shipment_id: str, tracking: str | None) -> None:
        client = self._get_client()
        # TODO: método real
        raise NotImplementedError("Completar update_invoice_with_zipnova() con el WSDL")