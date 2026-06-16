"""Page 2: Sales Forecast Management."""
import io
import streamlit as st
import pandas as pd
from datetime import date
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

DEST_OPTIONS = {"CC-长春": "CC", "DL-大连": "DL", "TJ-天津": "TJ"}
CUSTOMERS = ["CUST001", "CUST002", "CUST003"]
SKU_OPTIONS = ["SKU001"]  # single SKU demo; details managed in 系统管理

# Column name ↔ English key mapping (used for template and upload parsing)
_COL_MAP = {
    "货主编号*": "shipper_id",
    "客户编号*": "customer_id",
    "目的地代码*": "destination",
    "SKU编号*": "sku_id",
    "预测数量（托盘）*": "quantity_pallets",
    "要求交付日期*": "required_date",
}
_COL_MAP_INV = {v: k for k, v in _COL_MAP.items()}

_VALID_CUSTOMERS = {"CUST001", "CUST002", "CUST003"}
_VALID_DESTS = {"CC", "DL", "TJ"}
_VALID_SKUS = {"SKU001"}
_VALID_SHIPPERS = {"SH001", "SH002"}


def _make_excel_template() -> bytes:
    """Build an in-memory Excel workbook with two sheets: 预测数据 and 填写说明."""
    wb = openpyxl.Workbook()

    # ── Sheet 1: 预测数据 ──────────────────────────────────────────────────
    ws = wb.active
    ws.title = "预测数据"

    header_fill = PatternFill(start_color="1F5C99", end_color="1F5C99", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    center = Alignment(horizontal="center", vertical="center")

    headers = list(_COL_MAP.keys())
    col_widths = [16, 18, 18, 14, 22, 22]

    for col_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = width

    ws.row_dimensions[1].height = 24

    # Example row
    example = ["SH001", "CUST001", "CC", "SKU001", 15, "2026-06-23"]
    for col_idx, val in enumerate(example, start=1):
        cell = ws.cell(row=2, column=col_idx, value=val)
        cell.alignment = Alignment(horizontal="center")

    # Data validation — dropdowns for rows 2:1000
    dv_customer = DataValidation(
        type="list",
        formula1='"CUST001,CUST002,CUST003"',
        allow_blank=True,
        showDropDown=False,
        showErrorMessage=True,
        errorTitle="无效客户编号",
        error="请从下拉列表选择：CUST001 / CUST002 / CUST003",
    )
    dv_dest = DataValidation(
        type="list",
        formula1='"CC,DL,TJ"',
        allow_blank=True,
        showDropDown=False,
        showErrorMessage=True,
        errorTitle="无效目的地",
        error="请从下拉列表选择：CC（长春）/ DL（大连）/ TJ（天津）",
    )
    dv_sku = DataValidation(
        type="list",
        formula1='"SKU001"',
        allow_blank=False,
        showDropDown=False,
        showErrorMessage=True,
        errorTitle="无效SKU编号",
        error="请从下拉列表选择：SKU001",
    )
    dv_shipper = DataValidation(
        type="list",
        formula1='"SH001,SH002"',
        allow_blank=False,
        showDropDown=False,
        showErrorMessage=True,
        errorTitle="无效货主编号",
        error="请从下拉列表选择：SH001 / SH002",
    )
    dv_qty = DataValidation(
        type="whole",
        operator="between",
        formula1="1",
        formula2="500",
        allow_blank=True,
        showErrorMessage=True,
        errorTitle="无效数量",
        error="请填写 1–500 之间的整数",
    )

    ws.add_data_validation(dv_shipper)
    ws.add_data_validation(dv_customer)
    ws.add_data_validation(dv_dest)
    ws.add_data_validation(dv_sku)
    ws.add_data_validation(dv_qty)

    dv_shipper.sqref = "A2:A1000"
    dv_customer.sqref = "B2:B1000"
    dv_dest.sqref = "C2:C1000"
    dv_sku.sqref = "D2:D1000"
    dv_qty.sqref = "E2:E1000"

    # Freeze header row
    ws.freeze_panes = "A2"

    # ── Sheet 2: 填写说明 ──────────────────────────────────────────────────
    ws2 = wb.create_sheet("填写说明")
    ws2.title = "填写说明"

    title_font = Font(bold=True, size=13)
    ws2["A1"] = "预测录入Excel模板 — 填写说明"
    ws2["A1"].font = title_font
    ws2.merge_cells("A1:F1")

    guide_headers = ["列", "字段名称", "是否必填", "允许值", "格式说明", "示例"]
    gh_font = Font(bold=True, size=10)
    gh_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    for col_idx, h in enumerate(guide_headers, start=1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
        cell.font = gh_font
        cell.fill = gh_fill
        cell.alignment = center

    guide_rows = [
        ("A", "货主编号", "是（*）", "SH001 / SH002", "从下拉选择", "SH001"),
        ("B", "客户编号", "是（*）", "CUST001 / CUST002 / CUST003", "从下拉选择", "CUST001"),
        ("C", "目的地代码", "是（*）", "CC / DL / TJ", "CC=长春  DL=大连  TJ=天津", "CC"),
        ("D", "SKU编号", "是（*）", "SKU001", "从下拉选择", "SKU001"),
        ("E", "预测数量（托盘）", "是（*）", "1–500 整数", "托盘数，正整数", "15"),
        ("F", "要求交付日期", "是（*）",
         "日期，YYYY-MM-DD",
         "系统自动对齐至该周周一；例如填 2026-06-23（周二），存储为 2026-06-22（周一）",
         "2026-06-23"),
    ]

    ws2_col_widths = [6, 20, 12, 30, 52, 14]
    for col_idx, w in enumerate(ws2_col_widths, start=1):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = w

    for row_idx, row_data in enumerate(guide_rows, start=4):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws2.cell(row=row_idx, column=col_idx, value=val)
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    ws2.row_dimensions[1].height = 28
    for r in range(4, 10):
        ws2.row_dimensions[r].height = 36

    note_row = len(guide_rows) + 5
    ws2.cell(row=note_row, column=1, value="注意事项").font = Font(bold=True)
    notes = [
        "• 请勿修改第1行表头，否则上传时将无法识别列名",
        "• 第2行为示例数据，上传前请替换为实际数据（或直接在第3行起填写）",
        "• 日期列请使用 YYYY-MM-DD 格式，或 Excel 日期单元格格式均可",
        "• 上传后系统将展示解析预览，确认无误后再点击「确认提交」",
    ]
    for i, note in enumerate(notes, start=note_row + 1):
        ws2.cell(row=i, column=1, value=note)
        ws2.merge_cells(f"A{i}:F{i}")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


st.set_page_config(page_title="销售预测管理", page_icon="📈", layout="wide")
st.title("📈 销售预测管理")
st.caption("预测录入、置信度修正、订单确认")

tab1, tab2, tab3 = st.tabs(["预测录入", "预测列表", "订单确认"])

with tab1:
    st.subheader("新增销售预测")

    with st.form("new_forecast"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            customer = st.selectbox("客户", CUSTOMERS)
        with col2:
            dest_label = st.selectbox("目的地", list(DEST_OPTIONS.keys()))
        with col3:
            sku = st.selectbox("SKU", SKU_OPTIONS)
        with col4:
            qty = st.number_input("预测数量(托盘)", min_value=1, max_value=100, value=10)

        today = date.today()
        wcol1, wcol2 = st.columns(2)
        with wcol1:
            year = st.number_input("要求交付年份", min_value=2025, max_value=2030,
                                   value=today.year, step=1)
        with wcol2:
            max_week = date(int(year), 12, 28).isocalendar()[1]
            cur_week = today.isocalendar()[1]
            week_num = st.number_input("要求交付周（ISO周）", min_value=1,
                                       max_value=int(max_week),
                                       value=int(cur_week), step=1)
        due = date.fromisocalendar(int(year), int(week_num), 1)

        submitted = st.form_submit_button("提交预测")
        if submitted:
            st.success(f"预测已提交: {sku} {qty}托盘 → {dest_label}, 第 {week_num} 周（要求日期 {due}，周一）")

    st.divider()
    st.markdown("#### 批量导入")

    bcol1, bcol2 = st.columns([1, 3])
    with bcol1:
        st.download_button(
            label="📥 下载Excel模板",
            data=_make_excel_template(),
            file_name="预测录入模板.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with bcol2:
        uploaded = st.file_uploader(
            "上传填好的Excel文件（仅支持 .xlsx）",
            type=["xlsx"],
        )

    if uploaded is not None:
        try:
            df_raw = pd.read_excel(uploaded, sheet_name="预测数据", header=0)
        except Exception as e:
            st.error(f"无法读取文件：{e}，请确认上传的是从模板下载的 .xlsx 文件")
            st.stop()

        # Rename columns to English keys (strip * from required headers)
        rename_map = {}
        for col in df_raw.columns:
            key = _COL_MAP.get(col)
            if key:
                rename_map[col] = key
        df = df_raw.rename(columns=rename_map)

        # Drop fully-empty rows (users often leave example row or trailing blank rows)
        df = df.dropna(how="all").reset_index(drop=True)

        errors = []
        required_keys = ["shipper_id", "customer_id", "destination", "sku_id", "quantity_pallets", "required_date"]
        for key in required_keys:
            if key not in df.columns:
                errors.append(f"缺少必填列：**{_COL_MAP_INV.get(key, key)}**")
            elif df[key].isna().any():
                bad_rows = df.index[df[key].isna()].tolist()
                errors.append(f"列「{_COL_MAP_INV.get(key, key)}」第 {[r+2 for r in bad_rows]} 行存在空值")

        if "customer_id" in df.columns:
            invalid_cust = set(df["customer_id"].dropna().astype(str)) - _VALID_CUSTOMERS
            if invalid_cust:
                errors.append(f"无效客户编号：{invalid_cust}，允许值为 CUST001 / CUST002 / CUST003")

        if "destination" in df.columns:
            invalid_dest = set(df["destination"].dropna().astype(str)) - _VALID_DESTS
            if invalid_dest:
                errors.append(f"无效目的地代码：{invalid_dest}，允许值为 CC / DL / TJ")

        if "sku_id" in df.columns:
            invalid_sku = set(df["sku_id"].dropna().astype(str)) - _VALID_SKUS
            if invalid_sku:
                errors.append(f"无效SKU编号：{invalid_sku}，当前仅支持 SKU001")

        if errors:
            st.error("上传文件存在以下问题，请修正后重新上传：")
            for e in errors:
                st.markdown(f"- {e}")
        else:
            # Snap dates to Monday
            df["required_date"] = pd.to_datetime(df["required_date"]).apply(
                lambda d: (d - pd.Timedelta(days=d.weekday())).date()
            )
            df["sku_id"] = df["sku_id"].astype(str)
            if "quantity_pallets" in df.columns:
                df["quantity_pallets"] = df["quantity_pallets"].astype(int)

            display_cols = [c for c in
                ["shipper_id", "customer_id", "destination", "sku_id",
                 "quantity_pallets", "required_date"]
                if c in df.columns]
            display_headers = {k: v for v, k in _COL_MAP.items()}  # eng→zh

            st.success(f"解析成功，共 {len(df)} 条预测，请核对后提交")
            st.dataframe(
                df[display_cols].rename(columns={
                    "shipper_id": "货主编号",
                    "customer_id": "客户编号",
                    "destination": "目的地",
                    "sku_id": "SKU",
                    "quantity_pallets": "预测数量（托盘）",
                    "required_date": "要求日期（周一）",
                }),
                use_container_width=True,
                hide_index=True,
            )

            if st.button("✅ 确认提交全部预测", type="primary"):
                st.success(f"已提交 {len(df)} 条预测（Phase 2 接入引擎后将写入数据库）")

with tab2:
    st.subheader("已提交预测列表")
    st.dataframe(
        {
            "预测编号": ["F0001", "F0002", "F0003"],
            "客户": ["CUST001", "CUST002", "CUST003"],
            "目的地": ["CC", "DL", "TJ"],
            "SKU": ["SKU001", "SKU001", "SKU001"],
            "预测量": [15, 8, 20],
            "修正后": [13, 8, 17],
            "置信度": [0.85, 0.80, 0.82],
            "要求日期": ["2025-04-28", "2025-04-28", "2025-05-05"],
        },
        use_container_width=True, hide_index=True,
    )

with tab3:
    st.subheader("订单确认")
    st.caption("提交客户订单确认，后台自动匹配对应预测（无预测记录时也可提交）")

    with st.form("confirm_order"):
        col1, col2, col3 = st.columns(3)
        with col1:
            c_customer = st.selectbox("客户", CUSTOMERS)
        with col2:
            c_dest_label = st.selectbox("目的地", list(DEST_OPTIONS.keys()))
        with col3:
            c_sku = st.selectbox("SKU", SKU_OPTIONS)

        col4, col5 = st.columns(2)
        with col4:
            c_date = st.date_input("确认交付日期", value=date.today())
        with col5:
            c_qty = st.number_input("确认数量(托盘)", min_value=0, max_value=500, value=10)

        c_order_no = st.text_input("客户订单号", placeholder="如 PO-2026-00123")

        if st.form_submit_button("提交确认"):
            st.success(
                f"订单已提交：{c_customer} → {c_dest_label}，{c_sku}，"
                f"{c_date}，{c_qty} 托盘，订单号 {c_order_no}"
            )
