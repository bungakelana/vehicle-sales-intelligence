"""Buat flag dari kolom PII, lalu hapus PII dan kodekan salesman/SPV/leasing/customer."""
import hashlib

import pandas as pd

from .clean import plate_region
from .config import MONEY_COLS, MONEY_SCALE, PII_COLS

CORPORATE_PATTERN = r"^(?:PT|CV|UD|KOPERASI|KOP)\b\.?|\bTBK\b"


def _code_by_volume(s: pd.Series, prefix: str, width: int) -> dict:
    """Kode stabil: entitas dengan volume terbanyak mendapat nomor terkecil."""
    order = s.value_counts().index
    return {name: f"{prefix}{i:0{width}d}" for i, name in enumerate(order, 1)}


def _letter_codes(s: pd.Series, prefix: str) -> dict:
    order = s.value_counts().index
    return {name: f"{prefix}{chr(65 + i)}" for i, name in enumerate(order)}


def anonymize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    name = df["customer_name"].astype("string").str.upper().str.strip()
    df["is_corporate_name"] = name.str.contains(CORPORATE_PATTERN, regex=True, na=False)
    df["has_office_phone"] = df["phone_office"].notna() & (df["phone_office"].astype("string").str.strip() != "")
    df["stnk_same_as_buyer"] = name == df["stnk_name"].astype("string").str.upper().str.strip()
    df["plate_region"] = plate_region(df["plate_no"])

    df["salesman"] = df["salesman"].map(_code_by_volume(df["salesman"], "SLS-", 3))
    df["supervisor"] = df["supervisor"].map(_code_by_volume(df["supervisor"], "SPV-", 2))
    leasing_only = df.loc[df["leasing"] != "CASH", "leasing"]
    df["leasing"] = df["leasing"].map(_letter_codes(leasing_only, "LEASING-")).fillna("CASH")
    df["customer_id"] = df["customer_id"].map(lambda x: "CUST-" + hashlib.sha256(str(x).encode()).hexdigest()[:8])
    for c in ["invoice_no", "filling_number", "so_no", "book_no", "spk_no"]:
        df[c] = df[c].map(lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:10])
    for c in MONEY_COLS:
        df[c] = df[c] * MONEY_SCALE

    return df.drop(columns=PII_COLS + ["city"])
