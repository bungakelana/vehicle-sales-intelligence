"""Path & konstanta proyek."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYTICS = ROOT / "analytics"
RAW_DIR = ANALYTICS / "data" / "raw"
PROCESSED_DIR = ANALYTICS / "data" / "processed"
GEO_DIR = ANALYTICS / "data" / "geo"
SITE_DATA_DIR = ROOT / "site" / "public" / "data"
SITE_GEO_DIR = ROOT / "site" / "public" / "geo"

CLEAN_PARQUET = PROCESSED_DIR / "sales_clean.parquet"
CITY_MAPPING = GEO_DIR / "city_mapping.csv"
RAW_GEOJSON = GEO_DIR / "IDN_adm_2_kabkota.json"

# Faktor skala rupiah untuk menyamarkan angka finansial (1.0 = tidak diskalakan; data dummy sudah sintetis)
MONEY_SCALE = 1.0

SLA_STNK_DAYS = 30
FORECAST_HORIZON = 6
HOLDOUT_MONTHS = 6
N_CLUSTERS = 4
RANDOM_STATE = 42

# Budget ukuran (byte, gzip)
JSON_BUDGET_GZ = 300 * 1024
GEO_BUDGET = 150 * 1024

DISCLAIMER = "Data telah dianonimkan dan dimodifikasi untuk keperluan portofolio."

COLUMN_MAP = {
    "No.": "row_no", "Filling Number": "filling_number", "No. Faktur": "invoice_no",
    "Tgl Billing": "billing_date", "Spes No": "spec_no", "No SO": "so_no", "No Customer": "customer_id",
    "Nama Customer": "customer_name", "Address": "address", "City": "city", "Handphone": "phone_mobile",
    "Telp Rumah": "phone_home", "Telp Kantor": "phone_office", "Nama STNK": "stnk_name",
    "Alamat STNK": "stnk_address", "Chasis": "chassis_no", "No. Mesin": "engine_no",
    "Karoseri Spec.": "body_spec", "Color Description": "color", "Actual Physical GI Date": "actual_gi_date",
    "Tgl. GI": "gi_date", "Tgl.BSTK": "handover_date", "Leasing": "leasing", "Salesman name": "salesman",
    "SPV Name": "supervisor", "Sales Point": "sales_point", "Package Code": "package_code",
    "BookNumber": "book_no", "Jatuh Tempo": "due_date", "No Polisi": "plate_no", "No SPK": "spk_no",
    "Harga Unit": "unit_price", "Harga Discount": "price_after_discount", "Selesai STNK": "stnk_done_date",
    "Cabang Serah Terima": "handover_branch", "Total Discount": "total_discount",
}
DATE_COLS = ["billing_date", "actual_gi_date", "gi_date", "handover_date", "due_date", "stnk_done_date"]
MONEY_COLS = ["unit_price", "price_after_discount", "total_discount"]
PII_COLS = ["customer_name", "address", "phone_mobile", "phone_home", "phone_office", "stnk_name",
            "stnk_address", "chassis_no", "engine_no", "plate_no"]
