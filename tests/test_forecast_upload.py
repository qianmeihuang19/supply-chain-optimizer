"""Unit tests for the bulk-upload logic in 销售预测/预测录入."""
import io
import importlib.util
from datetime import date
from pathlib import Path

import openpyxl
import pandas as pd

# Load the page module by path (filename starts with a digit / Chinese chars)
_PAGE = Path(__file__).resolve().parent.parent / "app" / "pages" / "02_销售预测.py"
_spec = importlib.util.spec_from_file_location("forecast_page", _PAGE)
forecast_page = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(forecast_page)

make_template = forecast_page._make_excel_template
parse_and_validate = forecast_page.parse_and_validate
make_order_template = forecast_page._make_order_template
parse_and_validate_order = forecast_page.parse_and_validate_order
split_duplicates = forecast_page.split_duplicates
STORE_COLS = forecast_page.FORECAST_STORE_COLS

HEADERS = ["货主编号*", "客户编号*", "目的地代码*",
           "SKU编号*", "预测数量（托盘）*", "要求交付日期*"]
ORDER_HEADERS = ["货主编号*", "客户编号*", "目的地代码*", "SKU编号*",
                 "确认数量（托盘）*", "确认交付日期*", "客户订单号"]


def _df(*rows):
    """Build a raw upload DataFrame; each row is a 6-tuple in header order."""
    return pd.DataFrame(rows, columns=HEADERS)


def _odf(*rows):
    """Build a raw order-confirmation DataFrame; each row a 7-tuple."""
    return pd.DataFrame(rows, columns=ORDER_HEADERS)


VALID = ("SH001", "CUST001", "CC", "SKU001", 15, "2026-06-23")  # Tuesday
VALID_ORDER = ("SH001", "CUST001", "CC", "SKU001", 10, "2026-06-23", "PO-1")


def test_template_has_two_sheets():
    wb = openpyxl.load_workbook(io.BytesIO(make_template()))
    assert wb.sheetnames == ["预测数据", "填写说明"]
    ws = wb["预测数据"]
    assert [ws.cell(1, c).value for c in range(1, 7)] == HEADERS


def test_valid_data_passes_and_snaps_date_to_monday():
    df, errors = parse_and_validate(_df(VALID))
    assert errors == []
    assert df["required_date"].iloc[0] == date(2026, 6, 22)  # Tue -> Mon


def test_missing_value_is_rejected():
    df, errors = parse_and_validate(_df(("SH001", "CUST001", "CC", "SKU001", None, "2026-06-23")))
    assert df is None and errors


def test_invalid_enum_is_rejected():
    df, errors = parse_and_validate(_df(("SH001", "CUST999", "CC", "SKU001", 15, "2026-06-23")))
    assert df is None and errors


# ── Order confirmation ────────────────────────────────────────────────────
def test_order_template_has_two_sheets():
    wb = openpyxl.load_workbook(io.BytesIO(make_order_template()))
    assert wb.sheetnames == ["订单确认数据", "填写说明"]
    ws = wb["订单确认数据"]
    assert [ws.cell(1, c).value for c in range(1, 8)] == ORDER_HEADERS


def test_order_valid_data_passes_without_date_snap():
    df, errors = parse_and_validate_order(_odf(VALID_ORDER))
    assert errors == []
    # confirmed delivery date is NOT snapped to Monday (kept as actual date)
    assert df["confirmed_delivery_date"].iloc[0] == date(2026, 6, 23)


def test_order_optional_order_no_can_be_blank():
    df, errors = parse_and_validate_order(
        _odf(("SH001", "CUST001", "CC", "SKU001", 10, "2026-06-23", None)))
    assert errors == []


def test_order_invalid_enum_is_rejected():
    df, errors = parse_and_validate_order(
        _odf(("SH001", "CUST001", "XX", "SKU001", 10, "2026-06-23", "PO-1")))
    assert df is None and errors


# ── Duplicate detection ───────────────────────────────────────────────────
def _store(*rows):
    """Build a forecast store DataFrame; each row a 6-tuple in STORE_COLS order."""
    return pd.DataFrame(rows, columns=STORE_COLS)


R1 = ("SH001", "CUST001", "CC", "SKU001", 15, date(2026, 4, 27))
R2 = ("SH001", "CUST002", "DL", "SKU001", 8, date(2026, 4, 27))


def test_duplicate_against_existing_is_flagged():
    existing = _store(R1)
    to_add, dups = split_duplicates(existing, _store(R1))
    assert len(to_add) == 0 and len(dups) == 1


def test_distinct_rows_all_added():
    to_add, dups = split_duplicates(_store(R1), _store(R2))
    assert len(to_add) == 1 and len(dups) == 0


def test_duplicate_within_batch_is_flagged():
    to_add, dups = split_duplicates(_store(), _store(R1, R1, R2))
    assert len(to_add) == 2 and len(dups) == 1
