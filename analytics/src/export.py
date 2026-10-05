"""Bangun & tulis semua file JSON untuk website (kontrak data PROJECT_BRIEF Bagian 6.1)."""
import gzip
import json
from datetime import date

import numpy as np
import orjson
import pandas as pd
import statsmodels.formula.api as smf
from shapely.geometry import mapping, shape

from . import metrics as M
from .config import (DISCLAIMER, GEO_DIR, PII_COLS, RAW_GEOJSON, SITE_DATA_DIR, SITE_GEO_DIR,
                     SLA_STNK_DAYS)
from .models import cluster_kabupaten, detect_discount_anomalies, forecast_units


def r(x, n=4):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


def pct(x, n=1):
    return f"{x * 100:.{n}f}".replace(".", ",") + "%"


def rp(x):
    if abs(x) >= 1e12:
        return f"Rp {x / 1e12:.2f} T".replace(".", ",")
    if abs(x) >= 1e9:
        return f"Rp {x / 1e9:.1f} M".replace(".", ",")
    return f"Rp {x / 1e6:.0f} jt"


def columnar(df: pd.DataFrame) -> dict:
    return {"cols": list(df.columns), "rows": df.astype(object).where(df.notna(), None).values.tolist()}


# ---------------------------------------------------------------- per file
def build_meta(df):
    return {
        "period": {"start": df["billing_date"].min().strftime("%Y-%m-%d"),
                   "end": df["billing_date"].max().strftime("%Y-%m-%d")},
        "updated": date.today().isoformat(),
        "n_units": len(df),
        "disclaimer": DISCLAIMER,
        "filters": {
            "year_month": sorted(df["year_month"].unique()),
            "sales_point": sorted(df["sales_point"].unique()),
            "kabupaten": df["kabupaten_std"].value_counts().index.tolist(),
            "model_family": df["model_family"].value_counts().index.tolist(),
            "payment_type": ["Cash", "Leasing"],
        },
        "kpi_static": {k: r(v) for k, v in M.kpis(df).items()},
    }


def build_fact(df):
    d = df.assign(stnk_done=df["days_to_stnk"].notna(),
                  stnk_breach=df["days_to_stnk"] > SLA_STNK_DAYS)
    g = d.groupby(["year_month", "kabupaten_std", "model_family", "payment_type", "sales_point"])
    fact = g.agg(units=("invoice_no", "count"), gross=("unit_price", "sum"), discount=("total_discount", "sum"),
                 net=("net_price", "sum"), stnk_days_sum=("days_to_stnk", "sum"), stnk_n=("stnk_done", "sum"),
                 stnk_breach=("stnk_breach", "sum")).reset_index()
    for c in ["gross", "discount", "net"]:
        fact[c] = (fact[c] / 1e6).round(1)  # juta rupiah
    fact["stnk_days_sum"] = fact["stnk_days_sum"].astype(int)
    fact = fact.rename(columns={"kabupaten_std": "kabupaten"})
    return {"unit_money": "juta rupiah", **columnar(fact)}


def build_product(df):
    tree = df.groupby(["model_family", "body_spec", "color"]).size().rename("units").reset_index()
    heat = df.groupby(["kabupaten_std", "model_family"]).size().rename("units").reset_index()
    body_region = df.groupby(["kabupaten_std", "body_spec"]).size().rename("units").reset_index()
    colors = df["color"].value_counts()
    spec = df.groupby(["model_family", "spec_no"]).agg(units=("invoice_no", "count"),
                                                       avg_price=("unit_price", "mean")).reset_index()
    spec["avg_price"] = (spec["avg_price"] / 1e6).round(0)
    return {"tree": columnar(tree), "heat": columnar(heat), "body_region": columnar(body_region),
            "colors": [[k, int(v)] for k, v in colors.items()], "spec": columnar(spec)}


def build_discount(df):
    an = detect_discount_anomalies(df)
    fam_order = df["model_family"].value_counts().index.tolist()
    box = {f: M.box_stats(df.loc[df["model_family"] == f, "discount_pct"] * 100) for f in fam_order}
    bins = np.arange(0, 21, 1)
    hist, _ = np.histogram(df["discount_pct"] * 100, bins=bins)

    me = df.groupby("is_month_end").apply(lambda x: x["total_discount"].sum() / x["unit_price"].sum())
    week = df.groupby("week_of_month").agg(units=("invoice_no", "count"),
                                           disc=("total_discount", "sum"), price=("unit_price", "sum"))
    week["avg_disc"] = week["disc"] / week["price"]

    monthly = df.groupby(["year_month", "model_family"]).agg(
        units=("invoice_no", "count"), disc=("total_discount", "sum"), price=("unit_price", "sum")).reset_index()
    monthly["avg_disc_pct"] = monthly["disc"] / monthly["price"] * 100
    ols = smf.ols("units ~ avg_disc_pct + C(model_family)", data=monthly).fit()
    corr = float(monthly.groupby("model_family").apply(
        lambda x: x["units"].corr(x["avg_disc_pct"])).mean())

    pay = df.groupby("payment_type").apply(lambda x: x["total_discount"].sum() / x["unit_price"].sum())

    fam_med = df.groupby("model_family")["discount_pct"].transform("median")
    leak = (df.assign(excess=(df["discount_pct"] - fam_med) * 100,
                      excess_rp=df["total_discount"] - fam_med * df["unit_price"])
              .groupby("salesman").agg(units=("invoice_no", "count"), excess_pp=("excess", "mean"),
                                       excess_rp=("excess_rp", "sum")).reset_index()
              .sort_values("excess_pp", ascending=False))
    leak["excess_pp"] = leak["excess_pp"].round(2)
    leak["excess_rp"] = (leak["excess_rp"].clip(lower=0) / 1e6).round(1)

    anomalies = an[an["is_anomaly"]].sort_values("anomaly_score", ascending=False)
    me_excess = df[df["is_month_end"]]
    leakage_month_end = float(((me_excess["discount_pct"] - (me[False])) * me_excess["unit_price"]).clip(lower=0).sum())
    n_months = df["year_month"].nunique()
    return {
        "box": {"families": fam_order, "stats": [box[f] for f in fam_order]},
        "hist": {"bins": [f"{b}–{b + 1}%" for b in bins[:-1]], "counts": hist.tolist()},
        "month_end": {"avg_disc_month_end": r(me[True]), "avg_disc_other": r(me[False]),
                      "diff_pp": r((me[True] - me[False]) * 100, 2),
                      "leakage_per_month": r(leakage_month_end / n_months, 0),
                      "by_week": [[int(w), int(x.units), r(x.avg_disc)] for w, x in week.iterrows()]},
        "scatter": columnar(monthly[["year_month", "model_family", "units", "avg_disc_pct"]].round(2)),
        "regression": {"coef_units_per_pp": r(ols.params["avg_disc_pct"], 3),
                       "p_value": r(ols.pvalues["avg_disc_pct"], 4), "r2": r(ols.rsquared, 3),
                       "mean_within_family_corr": r(corr, 3),
                       "spec": "OLS: unit_bulanan ~ avg_diskon_% + fixed effect tipe unit"},
        "by_payment": {k: r(v) for k, v in pay.items()},
        "leakage": columnar(leak),
        "anomalies": columnar(anomalies.assign(discount_pct=(anomalies["discount_pct"] * 100).round(1),
                                               unit_price=(anomalies["unit_price"] / 1e6).round(0),
                                               z_family=anomalies["z_family"].round(1),
                                               billing_date=anomalies["billing_date"].dt.strftime("%Y-%m-%d"))
                              [["billing_date", "model_family", "salesman", "sales_point", "unit_price",
                                "discount_pct", "z_family"]]),
    }


def build_leasing(df):
    lease = df[df["payment_type"] == "Leasing"]
    share = lease["leasing"].value_counts(normalize=True)
    hhi = M.hhi(share)
    by_l = lease.groupby("leasing").agg(units=("invoice_no", "count"), net=("net_price", "sum"),
                                        term=("payment_term_days", "median"),
                                        stnk=("days_to_stnk", "median")).reindex(share.index)
    monthly = df.pivot_table(index="year_month", columns="payment_type", values="invoice_no",
                             aggfunc="count", fill_value=0).reset_index()
    kab = df.groupby("kabupaten_std").agg(units=("invoice_no", "count"),
                                          pct_leasing=("payment_type", lambda s: (s == "Leasing").mean()))
    kab = kab.sort_values("pct_leasing", ascending=False).reset_index()
    kab["pct_leasing"] = kab["pct_leasing"].round(3)
    last12 = df[df["billing_date"] > df["billing_date"].max() - pd.DateOffset(months=12)]
    l12 = last12[last12["payment_type"] == "Leasing"]
    return {
        "share": [[k, r(v), int(by_l.loc[k, "units"]), r(by_l.loc[k, "net"] / 1e6, 0),
                   r(by_l.loc[k, "term"], 0), r(by_l.loc[k, "stnk"], 0)] for k, v in share.items()],
        "share_cols": ["leasing", "share", "units", "net_jt", "median_term_days", "median_days_to_stnk"],
        "hhi": r(hhi, 0), "hhi_label": M.hhi_label(hhi), "top3_share": r(share.head(3).sum()),
        "pct_leasing": r((df["payment_type"] == "Leasing").mean()),
        "monthly": columnar(monthly),
        "by_kabupaten": columnar(kab),
        "stress_baseline": {
            "window": "12 bulan terakhir",
            "total_units": len(last12), "total_net_jt": r(last12["net_price"].sum() / 1e6, 0),
            "leasing_units": len(l12), "leasing_net_jt": r(l12["net_price"].sum() / 1e6, 0),
            "by_leasing": [[k, int(len(x)), r(x["net_price"].sum() / 1e6, 0)]
                           for k, x in l12.groupby("leasing")],
        },
    }


def build_salesforce(df):
    monthly = df.groupby(["salesman", "year_month"]).size().unstack(fill_value=0)
    s = df.groupby("salesman").agg(supervisor=("supervisor", "first"), sales_point=("sales_point", "first"),
                                   units=("invoice_no", "count"), net=("net_price", "sum"),
                                   disc=("total_discount", "sum"), price=("unit_price", "sum"),
                                   pct_leasing=("payment_type", lambda x: (x == "Leasing").mean()))
    s["avg_disc_pct"] = (s["disc"] / s["price"] * 100).round(2)
    s["net"] = (s["net"] / 1e9).round(2)
    s["pct_leasing"] = s["pct_leasing"].round(3)
    s["cv"] = monthly.apply(M.coef_variation, axis=1).round(2)
    s["quadrant"] = M.quadrant(s["units"], s["avg_disc_pct"])
    s = s.drop(columns=["disc", "price"]).sort_values("units", ascending=False).reset_index()

    def team(col):
        t = df.groupby(col).agg(units=("invoice_no", "count"), net=("net_price", "sum"),
                                disc=("total_discount", "sum"), price=("unit_price", "sum"),
                                salesmen=("salesman", "nunique"))
        t["avg_disc_pct"] = (t["disc"] / t["price"] * 100).round(2)
        t["net"] = (t["net"] / 1e9).round(2)
        return columnar(t.drop(columns=["disc", "price"]).sort_values("units", ascending=False).reset_index())

    return {"salesmen": columnar(s), "spv": team("supervisor"), "sales_point": team("sales_point"),
            "thresholds": {"units_median": float(s["units"].median()),
                           "disc_median": float(s["avg_disc_pct"].median())}}


def build_customers(df):
    seg = df.groupby("customer_type").agg(units=("invoice_no", "count"), customers=("customer_id", "nunique"),
                                          disc=("total_discount", "sum"), price=("unit_price", "sum"),
                                          leasing=("payment_type", lambda x: (x == "Leasing").mean()))
    seg["avg_disc_pct"] = (seg["disc"] / seg["price"] * 100).round(2)
    seg["leasing"] = seg["leasing"].round(3)
    fleet = df[df["customer_type"] == "Fleet/Corporate"].groupby("customer_id").agg(
        units=("invoice_no", "count"), net=("net_price", "sum"), last=("billing_date", "max"),
        kabupaten=("kabupaten_std", "first")).sort_values("units", ascending=False).head(10).reset_index()
    fleet["customer_id"] = [f"FLEET-{i:02d}" for i in range(1, len(fleet) + 1)]
    fleet["net"] = (fleet["net"] / 1e9).round(2)
    fleet["last"] = fleet["last"].dt.strftime("%Y-%m")
    return {"segments": columnar(seg.drop(columns=["disc", "price"]).reset_index()),
            "top_fleet": columnar(fleet),
            "pct_stnk_other_party": r(1 - df["stnk_same_as_buyer"].mean())}


STAGES = [("Billing → GI", "days_billing_to_gi"), ("GI → Physical GI", "days_gi_to_physical"),
          ("Physical GI → BSTK", "days_gi_to_handover")]


def build_leadtime(df):
    stages = [[name, r(df[c].median(), 1), r(df[c].quantile(0.9), 1), r(df[c].mean(), 2)] for name, c in STAGES]
    stnk = df["days_to_stnk"]
    stages.append(["Billing → STNK selesai", r(stnk.median(), 1), r(stnk.quantile(0.9), 1), r(stnk.mean(), 2)])
    branches = df["sales_point"].value_counts().index.tolist()
    leasings = df["leasing"].value_counts().index.tolist()
    breach_branch = df.groupby("sales_point")["days_to_stnk"].apply(lambda x: (x.dropna() > SLA_STNK_DAYS).mean())
    breach_leasing = df.groupby("leasing")["days_to_stnk"].apply(lambda x: (x.dropna() > SLA_STNK_DAYS).mean())
    karoseri = df.groupby("body_spec")["days_gi_to_physical"].median().sort_values(ascending=False)
    bottleneck = max(STAGES, key=lambda s: df[s[1]].mean())
    return {
        "stages": stages, "stage_cols": ["stage", "median", "p90", "mean"],
        "by_branch": {"names": branches,
                      "box": [M.box_stats(df.loc[df["sales_point"] == b, "days_to_stnk"]) for b in branches],
                      "breach": [r(breach_branch[b], 3) for b in branches]},
        "by_leasing": {"names": leasings,
                       "box": [M.box_stats(df.loc[df["leasing"] == lz, "days_to_stnk"]) for lz in leasings],
                       "breach": [r(breach_leasing[lz], 3) for lz in leasings]},
        "by_body": [[k, r(v, 1)] for k, v in karoseri.items()],
        "sla_days": SLA_STNK_DAYS,
        "pct_sla_breach": r(M.sla_breach_rate(df)),
        "pct_cross_branch": r(df["cross_branch"].mean()),
        "bottleneck_delivery_stage": bottleneck[0],
        "pending_stnk": int(stnk.isna().sum()),
    }


def build_geo_table(df):
    ind = pd.read_csv(GEO_DIR / "kabupaten_indicators.csv").set_index("kabupaten_std")
    g = df.groupby("kabupaten_std").agg(provinsi=("provinsi", "first"), geo_name=("geo_name", "first"),
                                        units=("invoice_no", "count"), net=("net_price", "sum"),
                                        disc=("total_discount", "sum"), price=("unit_price", "sum"),
                                        pct_leasing=("payment_type", lambda x: (x == "Leasing").mean()),
                                        cross=("cross_branch", "mean"))
    g["avg_disc_pct"] = (g["disc"] / g["price"] * 100).round(2)
    g["net"] = (g["net"] / 1e9).round(2)
    g["pct_leasing"] = g["pct_leasing"].round(3)
    g["cross"] = g["cross"].round(3)
    g = g.join(ind)
    riau = g["population_k"].notna()
    g["units_per_100k"] = (g["units"] / g["population_k"] * 100).round(1)
    # white space: selisih antara share populasi & share unit (hanya kabupaten Riau dengan data populasi)
    g["pop_share"] = g["population_k"] / g.loc[riau, "population_k"].sum()
    g["unit_share"] = g["units"] / g.loc[riau, "units"].sum()
    g["gap_units"] = ((g["pop_share"] - g["unit_share"]) * g.loc[riau, "units"].sum()).round(0)
    g = g.drop(columns=["disc", "price", "pop_share", "unit_share"]).sort_values("units", ascending=False)
    return g.reset_index()


def build_clusters(df, geo):
    cl = cluster_kabupaten(df)
    profile = cl.groupby("cluster_label").agg(n=("kabupaten_std", "count"), units=("units", "mean"),
                                              avg_discount_pct=("avg_discount_pct", "mean"),
                                              pct_leasing=("pct_leasing", "mean"), growth=("growth", "mean"))
    cl = cl.merge(geo[["kabupaten_std", "geo_name"]], on="kabupaten_std", how="left")
    return {"kabupaten": columnar(cl[["kabupaten_std", "geo_name", "units", "avg_discount_pct", "pct_leasing",
                                      "growth", "cluster_label"]].round(3)),
            "profiles": columnar(profile.round(3).reset_index())}


# ---------------------------------------------------------------- insights
def build_insights(df, geo, disc, leas, sf, lt, fc, cust):
    k = M.kpis(df)
    q = df.groupby("quarter").size()
    last_q, prev_q = q.index[-1], q.index[-2]
    q_growth = q.iloc[-1] / q.iloc[-2] - 1
    lastq_df = df[df["quarter"] == last_q]
    top_kab = lastq_df["kabupaten_std"].value_counts().index[0]
    top_fam = lastq_df["model_family"].value_counts().index[0]
    top5 = M.top_n_share(geo["units"], 5)
    riau = geo[geo["population_k"].notna()]
    ws = riau.sort_values("gap_units", ascending=False).iloc[0]
    reg = disc["regression"]
    me = disc["month_end"]
    lead = leas["share"][0]
    salesmen = pd.DataFrame(sf["salesmen"]["rows"], columns=sf["salesmen"]["cols"])
    stars = salesmen[salesmen["quadrant"] == "Star"]["salesman"].tolist()
    driven = salesmen[salesmen["quadrant"] == "Discount-driven"]["salesman"].tolist()
    leak_top = disc["leakage"]["rows"][0]
    worst_stage = max(lt["stages"][:3], key=lambda s: s[3])
    next3 = sum(f[1] for f in fc["forecast"][:3])
    seg = pd.DataFrame(cust["segments"]["rows"], columns=cust["segments"]["cols"]).set_index("customer_type")
    fleet_share = seg.loc["Fleet/Corporate", "units"] / seg["units"].sum()
    disc_effective = reg["p_value"] is not None and reg["p_value"] < 0.05 and reg["coef_units_per_pp"] > 0
    lease_rows = leas["stress_baseline"]
    at_risk_20 = lease_rows["leasing_net_jt"] * 0.2 * 1e6

    return {
        "hero": f"{pct(k['pct_leasing'], 0)} unit dibiayai leasing dan {pct(leas['top3_share'], 0)} di antaranya hanya "
                f"lewat 3 partner — ketika NPF industri naik ke ~3%, inilah titik rawan terbesar penjualan.",
        "overview": [
            f"Penjualan {last_q} {'naik' if q_growth >= 0 else 'turun'} {pct(abs(q_growth))} vs {prev_q}, "
            f"didorong oleh {top_kab} dan segmen {top_fam}.",
            f"Diskon rata-rata {pct(k['avg_discount_pct'])} dari harga unit, total {rp(k['discount'])} "
            f"selama periode data.",
            f"Fleet/Corporate menyumbang {pct(fleet_share, 0)} unit; {pct(k['pct_repeat_customer'], 0)} customer "
            f"melakukan repeat order.",
        ],
        "geography": [
            f"Top-5 kabupaten/kota menyumbang {pct(top5, 0)} unit — pasar terkonsentrasi di sekitar Pekanbaru.",
            f"White space terbesar: {ws['kabupaten_std']} ({ws['main_economy'].lower()}) — penetrasi "
            f"{str(ws['units_per_100k']).replace('.', ',')} unit/100 rb penduduk, potensi ±{int(ws['gap_units'])} unit "
            f"jika setara rata-rata Riau.",
            f"{pct(lt['pct_cross_branch'], 0)} unit diserahterimakan di cabang berbeda dari cabang penjual.",
        ],
        "discount": [
            f"Diskon di minggu terakhir bulan {str(me['diff_pp']).replace('.', ',')} poin persentase lebih tinggi "
            f"(potensi kebocoran ±{rp(me['leakage_per_month'])} per bulan).",
            ("Diskon lebih besar berasosiasi dengan volume lebih tinggi" if disc_effective else
             "Diskon lebih besar TIDAK terbukti menaikkan volume bulanan") +
            f" (koef. {str(reg['coef_units_per_pp']).replace('.', ',')} unit per +1 pp, p = "
            f"{str(reg['p_value']).replace('.', ',')}).",
            f"{leak_top[0]} memberi diskon rata-rata {str(leak_top[2]).replace('.', ',')} pp di atas median tipe "
            f"yang sama; {len(disc['anomalies']['rows'])} transaksi ditandai anomali.",
        ],
        "financing": [
            f"{pct(leas['pct_leasing'], 0)} unit dibiayai leasing; {lead[0]} sendiri menguasai {pct(lead[1], 0)} "
            f"transaksi kredit.",
            f"HHI leasing = {int(leas['hhi']):,} ({leas['hhi_label'].lower()}).".replace(",", "."),
            f"Jika approval leasing turun 20%, ±{round(lease_rows['leasing_units'] * 0.2)} unit / {rp(at_risk_20)} "
            f"net revenue per tahun berisiko.",
        ],
        "sales_team": [
            f"{len(stars)} salesman masuk kuadran Star (volume tinggi, diskon di bawah median): {', '.join(stars[:4])}.",
            f"{len(driven)} salesman volume tinggi tapi bergantung pada diskon — kandidat review approval diskon.",
            f"Rata-rata koefisien variasi penjualan bulanan {str(round(salesmen['cv'].mean(), 2)).replace('.', ',')}"
            f" — target bulanan perlu memperhitungkan musiman.",
        ],
        "operations": [
            f"Median billing → STNK selesai {int(k['median_days_to_stnk'])} hari; {pct(lt['pct_sla_breach'], 0)} unit "
            f"melewati SLA {lt['sla_days']} hari.",
            f"Tahap pengiriman paling lambat: {worst_stage[0]} (rata-rata {str(worst_stage[3]).replace('.', ',')} "
            f"hari, P90 {str(worst_stage[2]).replace('.', ',')} hari).",
            f"Unit leasing butuh waktu STNK lebih lama — dokumen kredit menjadi bottleneck administrasi.",
        ],
        "outlook": [
            f"Forecast 3 bulan ke depan ±{int(next3)} unit (MAPE holdout {pct(fc['mape'], 0)}).",
            "Fokus ekspansi ke kabupaten white space berbasis perkebunan dengan paket fleet & karoseri dump/tangki.",
            "Diversifikasi leasing partner untuk menurunkan risiko pengetatan kredit 2026.",
        ],
        "recommendations": [
            {"title": "Batas approval diskon akhir bulan",
             "body": f"Diskon minggu terakhir {str(me['diff_pp']).replace('.', ',')} pp lebih tinggi tanpa bukti "
                     f"kenaikan volume. Terapkan approval bertingkat > median+2 pp untuk menahan kebocoran "
                     f"±{rp(me['leakage_per_month'])}/bulan."},
            {"title": "Diversifikasi leasing partner",
             "body": f"Top-3 leasing = {pct(leas['top3_share'], 0)} transaksi kredit. Tambah 1–2 partner dengan NPF "
                     f"rendah (eligible DP 0% POJK 35/2025) dan siapkan program cash/fleet."},
            {"title": f"Ekspansi ke {ws['kabupaten_std']}",
             "body": f"Penetrasi masih rendah dibanding populasi; buka titik layanan/pameran dengan paket "
                     f"truk perkebunan."},
            {"title": "Coaching salesman discount-driven",
             "body": f"{len(driven)} salesman volume tinggi dengan diskon di atas median — jadikan pola Star "
                     f"sebagai benchmark dan kaitkan insentif dengan net price."},
            {"title": "Percepat dokumen STNK unit leasing",
             "body": f"{pct(lt['pct_sla_breach'], 0)} unit melewati SLA {lt['sla_days']} hari; buat SLA bersama "
                     f"leasing untuk penyerahan dokumen."},
        ],
    }


# ---------------------------------------------------------------- geo
def build_geojson(geo_names):
    raw = json.loads(RAW_GEOJSON.read_text(encoding="utf-8"))
    feats = []
    for f in raw["features"]:
        p = f["properties"]
        if p["NAME_1"] != "Riau":
            continue
        geom = shape(f["geometry"]).simplify(0.01, preserve_topology=True)
        gj = json.loads(json.dumps(mapping(geom)), parse_float=lambda x: round(float(x), 3))
        feats.append({"type": "Feature", "properties": {"name": p["NAME_2"]}, "geometry": gj})
    return {"type": "FeatureCollection", "features": feats}


# ---------------------------------------------------------------- write
def write_all(df: pd.DataFrame) -> dict:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SITE_GEO_DIR.mkdir(parents=True, exist_ok=True)
    geo = build_geo_table(df)
    disc = build_discount(df)
    leas = build_leasing(df)
    sf = build_salesforce(df)
    lt = build_leadtime(df)
    fc = forecast_units(df)
    cust = build_customers(df)
    files = {
        "meta.json": build_meta(df),
        "fact_monthly.json": build_fact(df),
        "geo.json": columnar(geo.round(4)),
        "product.json": build_product(df),
        "discount.json": disc,
        "leasing.json": leas,
        "salesforce.json": sf,
        "leadtime.json": lt,
        "forecast.json": fc,
        "clusters.json": build_clusters(df, geo),
        "customers.json": cust,
        "insights.json": build_insights(df, geo, disc, leas, sf, lt, fc, cust),
    }
    sizes = {}
    for name, obj in files.items():
        b = orjson.dumps(obj, option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NON_STR_KEYS)
        (SITE_DATA_DIR / name).write_bytes(b)
        sizes[name] = (len(b), len(gzip.compress(b)))
    gj = orjson.dumps(build_geojson(geo["geo_name"].dropna().unique()))
    (SITE_GEO_DIR / "riau_kabupaten.geojson").write_bytes(gj)
    sizes["geo/riau_kabupaten.geojson"] = (len(gj), len(gzip.compress(gj)))
    return sizes


def assert_no_pii(data_dir=SITE_DATA_DIR):
    banned = set(PII_COLS) | {"customer_name", "phone", "chassis", "engine_no", "plate_no", "address"}
    for f in data_dir.glob("*.json"):
        text = f.read_text(encoding="utf-8")
        hits = [b for b in banned if f'"{b}"' in text]
        if hits:
            raise AssertionError(f"Kolom PII ditemukan di {f.name}: {hits}")
