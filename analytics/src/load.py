"""Baca file Excel/CSV mentah dari data/raw dan rename kolom ke snake_case."""
import pandas as pd

from .config import COLUMN_MAP, RAW_DIR


def load_raw(raw_dir=RAW_DIR) -> pd.DataFrame:
    files = sorted(f for ext in ("*.xlsx", "*.xls", "*.csv") for f in raw_dir.glob(ext)
                   if not f.name.startswith("~$"))  # abaikan lock file Excel
    if not files:
        raise FileNotFoundError(f"Tidak ada file data di {raw_dir}")
    frames = [pd.read_csv(f, dtype=str) if f.suffix == ".csv" else pd.read_excel(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    missing = set(COLUMN_MAP) - set(df.columns)
    if missing:
        raise ValueError(f"Kolom tidak ditemukan: {sorted(missing)}")
    return df.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())]
