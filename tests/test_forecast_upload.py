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

HEADERS = ["货主编号*", "客户编号*", "目的地代码*",
           "SKU编号*", "预测数量（托盘）*", "要求交付日期*"]


def _df(*rows):
    """Build a raw upload DataFrame; each row is a 6-tuple in header order."""
    return pd.DataFrame(rows, columns=HEADERS)


VALID = ("SH001", "CUST001", "CC", "SKU001", 15, "2026-06-23")  # Tuesday


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
