## GBP → Zipnova Sync (Railway)

### Variables de entorno (Railway)
- GBP_WSDL_URL
- GBP_USER
- GBP_PASS

- ZIPNOVA_USER
- ZIPNOVA_PASS
- ZIPNOVA_ACCOUNT_ID
- ZIPNOVA_ORIGIN_ID
- ZIPNOVA_BASE_URL=https://api.zipnova.com.ar/v2

- GBP_LOGISTICS_ZIPNOVA_VALUE=ZIPNOVA
- SYNC_ENABLED=true
- SYNC_INTERVAL_SECONDS=60

- GENERIC_WEIGHT_KG=2
- GENERIC_HEIGHT_CM=10
- GENERIC_WIDTH_CM=20
- GENERIC_LENGTH_CM=30

### Run local
pip install -r requirements.txt
uvicorn app.main:app --reload
