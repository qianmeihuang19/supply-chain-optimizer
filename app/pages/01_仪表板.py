"""Page 1: KPI Dashboard — key performance indicators overview."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="KPI仪表板", page_icon="📊", layout="wide")
st.title("📊 KPI 仪表板")
st.caption("关键绩效指标一览")

st.subheader("核心KPI")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("按时交付率", "94.2%", "+1.5%")
with c2:
    st.metric("总发货成本", "¥328,500", "-3.2%")
with c3:
    st.metric("平均装载率", "78.5%", "+2.1%")
with c4:
    st.metric("ETA准确率", "91.0%", "+0.8%")
with c5:
    st.metric("预测准确率", "82.3%", "+1.2%")

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("各终端库存水位")
    inv_df = pd.DataFrame({
        "终端": ["长春 (CC)", "大连 (DL)", "天津 (TJ)"],
        "当前库存": [45, 38, 52],
        "安全库存": [12, 10, 8],
        "预置库存": [25, 20, 35],
        "已确认待配送": [15, 12, 12],
        "库存状态": ["充足", "充足", "充足"],
    })
    st.dataframe(inv_df, use_container_width=True, hide_index=True)

with col_right:
    st.subheader("待处理事项")
    st.warning("⚠️ 大连终端 2 笔订单到货未确认告警")
    st.info("ℹ️ 长春终端明日预计到达 15 托盘在途库存")
    st.success("✅ 所有终端库存水位正常")

st.markdown("---")

st.subheader("近期发货计划")
plan_df = pd.DataFrame({
    "计划编号": ["PLN0001", "PLN0002", "PLN0003"],
    "目的地": ["长春", "大连", "天津"],
    "类型": ["预置", "响应式", "预置"],
    "托盘数": [30, 15, 25],
    "计划发货": ["2025-04-20", "2025-04-21", "2025-04-20"],
    "状态": ["草稿", "已锁定", "草稿"],
})
st.dataframe(plan_df, use_container_width=True, hide_index=True)
