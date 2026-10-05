"""Feature engineering (PROJECT_BRIEF Bagian 7)."""
import numpy as np
import pandas as pd

FLEET_MIN_UNITS = 3

MODEL_FAMILY_PREFIX = {
    "PU": "Pickup", "LTD": "Light Truck 6-ban", "LT": "Light Truck 4-ban",
    "MT": "Medium Truck", "HT": "Heavy Truck",
}


def model_family(spec: pd.Series) -> pd.Series:
    prefix = spec.astype("string").str.extract(r"^([A-Z]+)")[0]
    return prefix.map(MODEL_FAMILY_PREFIX).fillna("Lainnya")


def _days(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a - b).dt.days


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["discount_pct"] = df["total_discount"] / df["unit_price"]
    df["net_price"] = df["unit_price"] - df["total_discount"]
    df["payment_type"] = np.where(df["leasing"] == "CASH", "Cash", "Leasing")

    df["units_per_customer"] = df.groupby("customer_id")["invoice_no"].transform("count")
    df["is_repeat"] = df["units_per_customer"] > 1
    df["customer_type"] = np.where(df["is_corporate_name"] | (df["units_per_customer"] >= FLEET_MIN_UNITS),
                                   "Fleet/Corporate", "Retail")

    df["days_billing_to_gi"] = _days(df["gi_date"], df["billing_date"])
    df["days_gi_to_physical"] = _days(df["actual_gi_date"], df["gi_date"])
    df["days_gi_to_handover"] = _days(df["handover_date"], df["actual_gi_date"])
    df["days_to_stnk"] = _days(df["stnk_done_date"], df["billing_date"])
    df["payment_term_days"] = _days(df["due_date"], df["billing_date"])
    df["cross_branch"] = df["sales_point"] != df["handover_branch"]

    bd = df["billing_date"]
    df["year_month"] = bd.dt.strftime("%Y-%m")
    df["quarter"] = bd.dt.year.astype(str) + "Q" + bd.dt.quarter.astype(str)
    df["week_of_month"] = ((bd.dt.day - 1) // 7 + 1).clip(upper=4)
    df["is_month_end"] = bd.dt.day > (bd.dt.days_in_month - 7)
    df["model_family"] = model_family(df["spec_no"])
    return df
