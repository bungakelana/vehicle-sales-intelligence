"""Cleaning & standarisasi: tanggal, angka, nama kota, nama leasing."""
import re

import pandas as pd

from .config import CITY_MAPPING, DATE_COLS, MONEY_COLS

CASH_TOKENS = {"", "CASH", "TUNAI", "KONTAN", "NAN", "NONE", "-"}

# Alias leasing -> nama baku (tambahkan saat menemukan varian baru)
LEASING_ALIASES = {
    "NUSANTARA FIN": "NUSANTARA FINANCE",
    "SINAR MITRA MF": "SINAR MITRA MULTIFINANCE",
}


def _norm_text(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.upper().str.replace(r"\s+", " ", regex=True)


def standardize_leasing(s: pd.Series) -> pd.Series:
    s = _norm_text(s).fillna("")
    s = s.str.replace(r"^PT\.?\s+", "", regex=True).str.strip()
    s = s.replace(LEASING_ALIASES)
    return s.where(~s.isin(CASH_TOKENS), "CASH")


def load_city_mapping(path=CITY_MAPPING) -> pd.DataFrame:
    m = pd.read_csv(path)
    m["city_raw"] = _norm_text(m["city_raw"])
    return m


def standardize_city(s: pd.Series, mapping: pd.DataFrame) -> pd.DataFrame:
    key = _norm_text(s)
    m = mapping.drop_duplicates("city_raw").set_index("city_raw")
    out = pd.DataFrame({
        "kabupaten_std": key.map(m["kabupaten_std"]),
        "provinsi": key.map(m["provinsi"]),
        "geo_name": key.map(m["geo_name"]),
    })
    unmapped = sorted(key[out["kabupaten_std"].isna()].dropna().unique())
    if unmapped:
        raise ValueError(f"City belum ada di city_mapping.csv: {unmapped}")
    return out


def clean(df: pd.DataFrame, mapping: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df.copy()
    for c in DATE_COLS:
        df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    for c in MONEY_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["spec_no", "body_spec", "color", "sales_point", "handover_branch", "package_code",
              "salesman", "supervisor", "customer_id", "invoice_no"]:
        df[c] = _norm_text(df[c])
    df["body_spec"] = df["body_spec"].fillna("CAB CHASSIS")
    df["leasing"] = standardize_leasing(df["leasing"])
    df = pd.concat([df, standardize_city(df["city"], mapping if mapping is not None else load_city_mapping())], axis=1)
    df = df.drop_duplicates("invoice_no", keep="first")
    return df.drop(columns=["row_no"])


def plate_region(s: pd.Series) -> pd.Series:
    return s.astype("string").str.extract(r"^\s*([A-Za-z]{1,2})\s*\d", flags=re.I)[0].str.upper()
