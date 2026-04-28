"""供应链计划优化系统 v3.2 - Streamlit主入口"""
import streamlit as st

st.set_page_config(
    page_title="供应链计划优化系统",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚛 供应链计划优化系统")
st.caption("v3.2 — 双引擎MIP优化 · 预置库存 · 到货告警 · 闭环反馈")
st.markdown("---")
st.info("请从左侧菜单选择功能模块")
