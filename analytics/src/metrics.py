"""Fungsi KPI & metrik bisnis."""
import numpy as np
import pandas as pd

from .config import SLA_STNK_DAYS


def kpis(df: pd.DataFrame) -> dict:
    return {
        "units": int(len(df)),
        "gross": float(df["unit_price"].sum()),
        "discount": float(df["total_discount"].sum()),
        "net": float(df["net_price"].sum()),
        "avg_discount_pct": float(df["total_discount"].sum() / df["unit_price"].sum()),
        "pct_leasing": float((df["payment_type"] == "Leasing").mean()),
        "median_days_to_stnk": float(df["days_to_stnk"].median()),
        "customers": int(df["customer_id"].nunique()),
        "pct_repeat_customer": float(df.groupby("customer_id")["is_repeat"].first().mean()),
        "pct_sla_breach": sla_breach_rate(df),
    }


def sla_breach_rate(df: pd.DataFrame, sla: int = SLA_STNK_DAYS) -> float:
    done = df["days_to_stnk"].dropna()
    return float((done > sla).mean()) if len(done) else float("nan")


def hhi(shares: pd.Series) -> float:
    """Herfindahl-Hirschman Index pada skala 0-10.000 (shares dalam proporsi 0-1)."""
    return float(((shares * 100) ** 2).sum())


def hhi_label(value: float) -> str:
    if value < 1500:
        return "Tidak terkonsentrasi"
    if value < 2500:
        return "Konsentrasi sedang"
    return "Sangat terkonsentrasi"


def top_n_share(units: pd.Series, n: int = 5) -> float:
    s = units.sort_values(ascending=False)
    return float(s.head(n).sum() / s.sum())


def coef_variation(x: pd.Series) -> float:
    m = x.mean()
    return float(x.std(ddof=0) / m) if m else float("nan")


def quadrant(units: pd.Series, disc: pd.Series) -> pd.Series:
    """Star = unit tinggi & diskon rendah; Discount-driven = unit tinggi & diskon tinggi; dst."""
    hi_u = units >= units.median()
    hi_d = disc >= disc.median()
    return pd.Series(np.select(
        [hi_u & ~hi_d, hi_u & hi_d, ~hi_u & ~hi_d],
        ["Star", "Discount-driven", "Efficient-low volume"],
        default="Needs coaching",
    ), index=units.index)


def box_stats(x: pd.Series) -> list[float]:
    """[min, Q1, median, Q3, max] dengan whisker 1,5 IQR (format boxplot ECharts)."""
    x = x.dropna()
    q1, med, q3 = x.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    lo = x[x >= q1 - 1.5 * iqr].min()
    hi = x[x <= q3 + 1.5 * iqr].max()
    return [round(float(v), 4) for v in (lo, q1, med, q3, hi)]
