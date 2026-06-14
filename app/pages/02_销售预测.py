"""Page 2: Sales Forecast Management."""
import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="销售预测管理", page_icon="📈", layout="wide")
st.title("📈 销售预测管理")
st.caption("预测录入、置信度修正、订单确认")

tab1, tab2, tab3 = st.tabs(["预测录入", "预测列表", "订单确认"])

with tab1:
    st.subheader("新增销售预测")

    # Date precision selector outside the form so it can control the form layout
    precision = st.radio("交付日期精度", ["天", "周"], horizontal=True)

    with st.form("new_forecast"):
        col1, col2, col3 = st.columns(3)
        with col1:
            customer = st.selectbox("客户", ["CUST001", "CUST002", "CUST003"])
        with col2:
            dest = st.selectbox("目的地", ["CC-长春", "DL-大连", "TJ-天津"])
        with col3:
            qty = st.number_input("预测数量(托盘)", min_value=1, max_value=100, value=10)

        if precision == "天":
            due = st.date_input("要求交付日期")
            date_precision = "day"
        else:
            today = date.today()
            wcol1, wcol2 = st.columns(2)
            with wcol1:
                year = st.number_input("年份", min_value=2025, max_value=2030,
                                       value=today.year, step=1)
            with wcol2:
                max_week = date(int(year), 12, 28).isocalendar()[1]
                cur_week = today.isocalendar()[1]
                week_num = st.number_input("第几周（ISO周）", min_value=1,
                                           max_value=int(max_week),
                                           value=int(cur_week), step=1)
            # date.fromisocalendar(year, week, weekday): 3 = Wednesday
            due = date.fromisocalendar(int(year), int(week_num), 3)
            st.caption(f"实际存储日期：**{due}**（第 {week_num} 周周三）")
            date_precision = "week"

        submitted = st.form_submit_button("提交预测")
        if submitted:
            st.success(f"预测已提交: {qty}托盘 → {dest}, 交付日 {due}（精度：{precision}）")

with tab2:
    st.subheader("已提交预测列表")
    st.info("此处显示已录入的销售预测及置信度修正后数量")
    st.dataframe(
        {
            "预测编号": ["F0001", "F0002", "F0003"],
            "客户": ["CUST001", "CUST002", "CUST003"],
            "目的地": ["CC", "DL", "TJ"],
            "预测量": [15, 8, 20],
            "修正后": [13, 8, 17],
            "置信度": [0.85, 0.80, 0.82],
            "要求日期": ["2025-04-28", "2025-04-30", "2025-05-01"],
        },
        use_container_width=True, hide_index=True,
    )

with tab3:
    st.subheader("订单确认")
    st.info("客户在此提交最终确认数量")
    with st.form("confirm_order"):
        forecast_id = st.text_input("预测编号", placeholder="F0001")
        conf_qty = st.number_input("确认数量(托盘)", min_value=0, max_value=100, value=10)
        if st.form_submit_button("确认订单"):
            st.success(f"订单 {forecast_id} 已确认: {conf_qty} 托盘")
