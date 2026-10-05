import pandas as pd

from src import metrics as M
from src.clean import plate_region, standardize_leasing


def test_hhi_monopoly_and_even():
    assert M.hhi(pd.Series([1.0])) == 10000
    assert round(M.hhi(pd.Series([0.25] * 4))) == 2500


def test_top_n_share():
    assert M.top_n_share(pd.Series([50, 30, 10, 5, 5]), 2) == 0.8


def test_quadrant_labels():
    q = M.quadrant(pd.Series([10, 10, 1, 1]), pd.Series([1.0, 9.0, 1.0, 9.0]))
    assert q.tolist() == ["Star", "Discount-driven", "Efficient-low volume", "Needs coaching"]


def test_standardize_leasing_cash_tokens():
    s = standardize_leasing(pd.Series(["cash", None, "TUNAI", "PT. BINA ARTHA LEASING", "NUSANTARA FIN"]))
    assert s.tolist() == ["CASH", "CASH", "CASH", "BINA ARTHA LEASING", "NUSANTARA FINANCE"]


def test_plate_region():
    assert plate_region(pd.Series(["BM 8123 AB", "b 1234 xy", None])).tolist()[:2] == ["BM", "B"]
