"""Supply Chain Optimization System v3.2 - Streamlit main entry."""
import sys
from pathlib import Path

import streamlit as st

# Ensure src is importable
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

st.set_page_config(
    page_title="供应链计划优化系统",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚛 供应链计划优化系统")
st.caption("v3.2 — 双引擎MIP优化 · 预置库存 · 到货告警 · 闭环反馈")
st.markdown("---")

# System status summary
st.subheader("系统概览")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("目标交付天数 x", "2 天", help="从订单确认到送达的最大天数")
with col2:
    st.metric("发货点", "上海 (SH)")
with col3:
    st.metric("终端数量", "3 个")
with col4:
    st.metric("模拟SKU", "1 个")

st.markdown("---")
st.info("👈 请从左侧菜单选择功能模块")

# Quick status table
st.subheader("终端状态一览")
import pandas as pd
status_df = pd.DataFrame({
    "终端": ["长春 (CC)", "大连 (DL)", "天津 (TJ)"],
    "在途天数(正常)": [4, 3, 2],
    "在途天数(冬季)": [5, 4, 3],
    "本地配送": ["1天", "1天", "1天"],
    "x=1 需提前": ["4天", "3天", "2天"],   # transit-(x-local) = transit-(1-1)
    "x=2 需提前": ["3天", "2天", "1天"],   # transit-(2-1)
    "x=3 需提前": ["2天", "1天", "不需要"],  # transit-(3-1), TJ=0
})
st.dataframe(status_df, use_container_width=True, hide_index=True)
