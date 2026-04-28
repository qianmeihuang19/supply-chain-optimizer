"""Page 4: Waybill Tracking."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="运单跟踪", page_icon="🚚", layout="wide")
st.title("🚚 运单跟踪")
st.caption("在途运单列表、ETA vs ATA 对比、承运商准时率")

tab1, tab2 = st.tabs(["在途运单", "承运商准时率"])

with tab1:
    st.subheader("在途运单")
    st.dataframe({
        "运单号": ["WB0001", "WB0002", "WB0003"],
        "计划编号": ["PLN0001", "PLN0002", "PLN0003"],
        "目的地": ["长春", "大连", "天津"],
        "承运商": ["CR001", "CR002", "CR001"],
        "发货时间": ["2025-04-20 08:00"] * 3,
        "ETA": ["2025-04-24 08:00", "2025-04-23 08:00", "2025-04-22 08:00"],
        "ATA": ["—", "—", "—"],
        "状态": ["在途", "在途", "在途"],
    }, use_container_width=True, hide_index=True)

    st.subheader("ETA vs ATA 对比图")
    st.caption("历史ETA准确率趋势")
    st.line_chart({
        "日期": pd.date_range("2025-04-01", periods=20),
        "ETA偏差(小时)": [0, -2, 1, 3, -1, 0, 5, -3, 2, 1, 0, -1, 4, -2, 0, 3, -1, 0, 2, -1],
    })

with tab2:
    st.subheader("承运商准时率统计")
    st.dataframe({
        "承运商": ["CR001", "CR002"],
        "运单数": [45, 38],
        "准时率": ["92.1%", "89.5%"],
        "平均ETA偏差": ["1.2h", "2.5h"],
        "可靠性评分": [92, 87],
    }, use_container_width=True, hide_index=True)
