"""Page 3: Shipment Plan Workbench — core optimization page."""
import streamlit as st

st.set_page_config(page_title="发货计划工作台", page_icon="📦", layout="wide")
st.title("📦 发货计划工作台")
st.caption("引擎一: 发货计划MIP优化")

tab1, tab2, tab3, tab4 = st.tabs([
    "待优化订单池", "优化结果", "x值敏感性分析", "装载方案",
])

with tab1:
    st.subheader("待优化订单池（按目的地分组）")
    st.dataframe({
        "目的地": ["CC", "CC", "DL", "DL", "TJ", "TJ"],
        "客户": ["CUST001", "CUST002", "CUST001", "CUST003", "CUST002", "CUST003"],
        "预测量": [15, 8, 12, 20, 10, 6],
        "修正后": [13, 7, 10, 16, 9, 5],
        "要求日期": ["2025-05-01"] * 6,
        "预置深度(天)": [2, 2, 1, 1, 1, 1],
    }, use_container_width=True, hide_index=True)

    if st.button("🚀 运行优化", type="primary"):
        st.success("优化完成！请查看「优化结果」标签页")

with tab2:
    st.subheader("优化结果 — 推荐方案")
    st.metric("总成本", "¥45,800")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("运费", "¥32,000")
    with c2:
        st.metric("存储成本", "¥5,400")
    with c3:
        st.metric("违约成本", "¥0")
    with c4:
        st.metric("装载率", "82.5%")

    st.dataframe({
        "计划编号": ["PLN0001", "PLN0002", "PLN0003"],
        "目的地": ["CC", "DL", "TJ"],
        "类型": ["preposition", "preposition", "preposition"],
        "托盘数": [30, 22, 24],
        "车辆": ["V0001", "V0006", "V0011"],
        "运费": ["¥12,000", "¥10,000", "¥8,000"],
        "装载率": ["85%", "78%", "80%"],
    }, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("x值敏感性分析")
    st.caption("拖动x值查看总成本变化")
    x_val = st.slider("目标交付天数 x", min_value=1, max_value=7, value=2)
    st.info(f"x={x_val} 时，预置提前量: 长春={max(0,4-(x_val-1))}天, 大连={max(0,3-(x_val-1))}天, 天津={max(0,2-(x_val-1))}天")
    st.line_chart({"x值": list(range(1, 8)), "总成本(万元)": [6.5, 4.6, 3.8, 3.5, 3.3, 3.2, 3.1]})

with tab4:
    st.subheader("装载方案可视化")
    st.info("车辆装载率计算结果")
    st.dataframe({
        "车辆": ["V0001", "V0006", "V0011"],
        "车型": ["40ft_container", "40ft_container", "40ft_container"],
        "最大托盘": [36, 36, 36],
        "实际装载": [30, 22, 24],
        "装载率": ["83.3%", "61.1%", "66.7%"],
    }, use_container_width=True, hide_index=True)
