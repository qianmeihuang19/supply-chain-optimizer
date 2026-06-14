"""Page 2: Sales Forecast Management."""
import streamlit as st
from datetime import date

DEST_OPTIONS = {"CC-长春": "CC", "DL-大连": "DL", "TJ-天津": "TJ"}
CUSTOMERS = ["CUST001", "CUST002", "CUST003"]
SKU_OPTIONS = ["SKU001"]  # single SKU demo; details managed in 系统管理

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
            st.success(f"预测已提交: {sku} {qty}托盘 → {dest_label}, 第 {week_num} 周")

with tab2:
    st.subheader("已提交预测列表")
    st.info("此处显示已录入的销售预测及置信度修正后数量")
    st.dataframe(
        {
            "预测编号": ["F0001", "F0002", "F0003"],
            "客户": ["CUST001", "CUST002", "CUST003"],
            "目的地": ["CC", "DL", "TJ"],
            "SKU": ["SKU001", "SKU001", "SKU001"],
            "预测量": [15, 8, 20],
            "修正后": [13, 8, 17],
            "置信度": [0.85, 0.80, 0.82],
            "要求日期": ["2025-04-28", "2025-04-30", "2025-05-01"],
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
