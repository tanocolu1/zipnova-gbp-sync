from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # GBP WS
    GBP_WSDL_URL: str
    GBP_USER: str
    GBP_PASS: str

    # Criterios de filtrado
    GBP_LOGISTICS_ZIPNOVA_VALUE: str = "ZIPNOVA"   # el valor exacto como figure en GBP
    GBP_ONLY_FACTURADO: bool = True               # si querés desactivar el filtro

    # Zipnova
    ZIPNOVA_BASE_URL: str = "https://api.zipnova.com.ar/v2"
    ZIPNOVA_USER: str
    ZIPNOVA_PASS: str
    ZIPNOVA_ACCOUNT_ID: int
    ZIPNOVA_ORIGIN_ID: int

    # Bulto genérico
    GENERIC_WEIGHT_KG: float = 2.0
    GENERIC_HEIGHT_CM: float = 10.0
    GENERIC_WIDTH_CM: float = 20.0
    GENERIC_LENGTH_CM: float = 30.0

    # Scheduler
    SYNC_ENABLED: bool = True
    SYNC_INTERVAL_SECONDS: int = 60

settings = Settings()
