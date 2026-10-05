"""Forecast (SARIMA), clustering kabupaten (KMeans), dan anomaly detection diskon (IsolationForest)."""
import warnings

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX

from .config import FORECAST_HORIZON, HOLDOUT_MONTHS, N_CLUSTERS, RANDOM_STATE


def monthly_units(df: pd.DataFrame) -> pd.Series:
    s = df.set_index("billing_date").resample("MS")["invoice_no"].count()
    s.index.freq = "MS"
    return s.astype(float)


def _fit(y: pd.Series):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        seasonal = (0, 1, 1, 12) if len(y) >= 26 else (0, 0, 0, 0)
        return SARIMAX(y, order=(1, 1, 1), seasonal_order=seasonal,
                       enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)


def forecast_units(df: pd.DataFrame, horizon: int = FORECAST_HORIZON, holdout: int = HOLDOUT_MONTHS) -> dict:
    y = monthly_units(df)
    train, test = y.iloc[:-holdout], y.iloc[-holdout:]
    pred_test = _fit(train).get_forecast(holdout).predicted_mean.clip(lower=0)
    mape = float((np.abs(test - pred_test) / test.replace(0, np.nan)).mean())

    fc = _fit(y).get_forecast(horizon)
    ci = fc.conf_int(alpha=0.2).clip(lower=0)
    return {
        "actual": [[d.strftime("%Y-%m"), int(v)] for d, v in y.items()],
        "holdout_pred": [[d.strftime("%Y-%m"), round(float(v), 1)] for d, v in pred_test.items()],
        "forecast": [[d.strftime("%Y-%m"), round(float(m), 1), round(float(lo), 1), round(float(hi), 1)]
                     for d, m, lo, hi in zip(fc.predicted_mean.index, fc.predicted_mean.clip(lower=0),
                                              ci.iloc[:, 0], ci.iloc[:, 1])],
        "mape": round(mape, 4),
        "model": "SARIMA(1,1,1)(0,1,1,12)",
        "interval": "80%",
    }


CLUSTER_FEATURES = ["units", "avg_discount_pct", "pct_leasing", "growth"]


def cluster_kabupaten(df: pd.DataFrame, k: int = N_CLUSTERS, min_units: int = 20) -> pd.DataFrame:
    last = df["billing_date"].max()
    recent = df["billing_date"] > last - pd.DateOffset(months=12)
    prior = (df["billing_date"] <= last - pd.DateOffset(months=12)) & (df["billing_date"] > last - pd.DateOffset(months=24))
    g = df.groupby("kabupaten_std")
    feat = pd.DataFrame({
        "units": g.size(),
        "avg_discount_pct": g["total_discount"].sum() / g["unit_price"].sum(),
        "pct_leasing": g["payment_type"].apply(lambda s: (s == "Leasing").mean()),
        "growth": (df[recent].groupby("kabupaten_std").size() + 1) / (df[prior].groupby("kabupaten_std").size() + 1) - 1,
    }).fillna(0)
    feat["growth"] = feat["growth"].clip(-1, 1.5)
    # Kabupaten dengan unit terlalu sedikit membuat centroid tidak stabil -> tidak ikut clustering
    small = feat["units"] < min_units
    fit = feat[~small].copy()
    X = StandardScaler().fit_transform(fit[CLUSTER_FEATURES])
    fit["cluster"] = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit_predict(X)

    # Beri label bisnis berdasarkan centroid (greedy, setiap label dipakai sekali)
    cent = fit.groupby("cluster")[CLUSTER_FEATURES].mean()
    z = (cent - fit[CLUSTER_FEATURES].mean()) / fit[CLUSTER_FEATURES].std(ddof=0)
    labels, remaining = {}, list(cent.index)
    for label, col in [("Core market", "units"), ("Growth market", "growth"),
                       ("Credit-dependent", "pct_leasing"), ("Price-sensitive", "avg_discount_pct")]:
        if not remaining:
            break
        c = z.loc[remaining, col].idxmax()
        labels[c] = label if z.loc[c, col] > 0 else "Stable market"
        remaining.remove(c)
    fit["cluster_label"] = fit["cluster"].map(labels).fillna("Lainnya")
    feat = feat.join(fit[["cluster", "cluster_label"]])
    feat["cluster_label"] = feat["cluster_label"].fillna("Data terbatas")
    return feat.reset_index()


def detect_discount_anomalies(df: pd.DataFrame, contamination: float = 0.02) -> pd.DataFrame:
    fam_med = df.groupby("model_family")["discount_pct"].transform("median")
    fam_std = df.groupby("model_family")["discount_pct"].transform("std")
    X = pd.DataFrame({
        "discount_pct": df["discount_pct"],
        "disc_vs_family": df["discount_pct"] - fam_med,
        "log_price": np.log(df["unit_price"]),
        "is_month_end": df["is_month_end"].astype(int),
    })
    iso = IsolationForest(contamination=contamination, random_state=RANDOM_STATE).fit(X)
    out = df.copy()
    out["anomaly_score"] = -iso.score_samples(X)
    out["z_family"] = (df["discount_pct"] - fam_med) / fam_std
    out["is_anomaly"] = (iso.predict(X) == -1) & (out["z_family"] > 1.5)
    return out
