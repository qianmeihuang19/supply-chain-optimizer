"""Page 6: Terminal Inventory & Transfer (Engine 2)."""
import streamlit as st

st.set_page_config(page_title="终端库存与调拨", page_icon="🏭", layout="wide")
st.title("🏭 终端库存与调拨")
st.caption("引擎二: 终端调拨MIP优化 · 库存状态 · 差异分析")

tab1, tab2, tab3 = st.tabs(["终端库存状态", "调拨优化", "生产计划建议"])

with tab1:
    st.subheader("各终端实时库存")
    st.dataframe({
        "终端": ["长春 (CC)", "大连 (DL)", "天津 (TJ)"],
        "当前库存": [45, 38, 52],
        "安全库存": [12, 10, 8],
        "预置库存": [25, 20, 35],
        "已确认待配送": [15, 12, 12],
        "等待确认": [5, 6, 5],
        "剩余库存": [0, 0, 0],
        "存储天数": [3, 2, 1],
    }, use_container_width=True, hide_index=True)

    st.subheader("订单确认 vs 销售预测差异分析")
    st.dataframe({
        "终端": ["CC", "DL", "TJ"],
        "总预测量": [450, 380, 520],
        "总确认量": [420, 360, 480],
        "偏差率": ["-6.7%", "-5.3%", "-7.7%"],
        "偏差方向": ["低于预测", "低于预测", "低于预测"],
    }, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("调拨优化方案")
    if st.button("🚀 运行调拨优化", type="primary"):
        st.success("调拨优化完成！")

    st.dataframe({
        "调拨编号": ["TRF0001", "TRF0002"],
        "来源": ["大连(DL)", "天津(TJ)"],
        "目标": ["长春(CC)", "长春(CC)"],
        "数量": [8, 5],
        "调拨成本": ["¥640", "¥500"],
        "状态": ["计划中", "计划中"],
    }, use_container_width=True, hide_index=True)

    st.subheader("成本明细")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("调拨成本", "¥1,140")
    with c2:
        st.metric("存储节省", "¥450")
    with c3:
        st.metric("净成本", "¥690")

with tab3:
    st.subheader("生产计划调整建议")
    st.info("基于订单确认与预测偏差，建议客户调整生产计划")
    st.dataframe({
        "客户": ["CUST001", "CUST002", "CUST003"],
        "终端": ["CC", "DL", "TJ"],
        "建议调整": ["减少10%", "维持", "减少8%"],
        "依据": ["系统性多报15%", "偏差正常", "多报约12%"],
    }, use_container_width=True, hide_index=True)
