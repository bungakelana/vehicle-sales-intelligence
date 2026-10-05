"""Satu perintah: raw -> clean -> anonim -> features -> JSON siap web.

    cd analytics && python build_data.py
"""
import sys

from src.anonymize import anonymize
from src.clean import clean
from src.config import CLEAN_PARQUET, GEO_BUDGET, JSON_BUDGET_GZ, PII_COLS
from src.export import assert_no_pii, write_all
from src.features import add_features
from src.load import load_raw


def main() -> int:
    raw = load_raw()
    df = anonymize(clean(raw))
    assert not set(PII_COLS) & set(df.columns), "PII masih ada di data processed"
    CLEAN_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEAN_PARQUET, index=False)

    df = add_features(df)
    sizes = write_all(df)
    assert_no_pii()

    data_gz = sum(gz for name, (_, gz) in sizes.items() if not name.startswith("geo/"))
    geo_raw = sizes["geo/riau_kabupaten.geojson"][0]
    for name, (raw_b, gz) in sizes.items():
        print(f"  {name:32s} {raw_b / 1024:7.1f} KB  (gzip {gz / 1024:6.1f} KB)")
    print(f"Rows: {len(raw)} raw -> {len(df)} clean | data gzip {data_gz / 1024:.1f} KB | geo {geo_raw / 1024:.1f} KB")
    ok = data_gz <= JSON_BUDGET_GZ and geo_raw <= GEO_BUDGET
    print("Budget OK" if ok else "BUDGET TERLAMPAUI")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
