"""Page 8: Analytics & Reports — forecast accuracy trends."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="分析报表", page_icon="📋", layout="wide")
st.title("📋 分析报表")
st.caption("预测准确率趋势 · 成本分析 · 优化效果对比")

tab1, tab2, tab3 = st.tabs(["预测准确率", "成本趋势", "优化效果对比"])

with tab1:
    st.subheader("预测准确率趋势（按客户/终端）")
    dates = pd.date_range("2025-04-01", periods=30)
    df_accuracy = pd.DataFrame({
        "CUST001": [78 + i * 0.2 for i in range(30)],
        "CUST002": [82 + i * 0.15 for i in range(30)],
        "CUST003": [85 + i * 0.1 for i in range(30)],
    }, index=dates)
    st.line_chart(df_accuracy)

    st.subheader("按终端统计")
    st.dataframe({
        "终端": ["CC", "DL", "TJ"],
        "预测量": [450, 380, 520],
        "确认量": [420, 360, 480],
        "准确率": ["93.3%", "94.7%", "92.3%"],
        "偏差方向": ["低于预测", "低于预测", "低于预测"],
    }, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("总成本趋势")
    df_cost = pd.DataFrame({
        "运费(万)": [32.8, 31.5],
        "存储成本(万)": [5.4, 4.8],
        "违约成本(万)": [0.0, 0.0],
    }, index=["4月", "5月"])
    st.line_chart(df_cost)

with tab3:
    st.subheader("优化前 vs 优化后")
    st.dataframe({
        "指标": ["总成本", "平均装载率", "按时交付率", "库存周转天数"],
        "优化前": ["¥45,200", "62.0%", "88.5%", "8.2天"],
        "优化后": ["¥38,500", "78.5%", "94.2%", "5.1天"],
        "改善": ["-14.8%", "+26.6%", "+6.4%", "-37.8%"],
    }, use_container_width=True, hide_index=True)
