"""Page 3: Shipment Plan Workbench — core optimization page."""
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="发货计划工作台", page_icon="📦", layout="wide")
st.title("📦 发货计划工作台")
st.caption("引擎一: 发货计划MIP优化")

tab1, tab2, tab3 = st.tabs([
    "待优化订单池", "优化结果", "装载方案",
])

# Mock forecast pool — more rows to make selection meaningful
_MOCK_FORECASTS = pd.DataFrame({
    "预测编号": ["F0001","F0002","F0003","F0004","F0005","F0006","F0007","F0008","F0009"],
    "目的地":   ["CC","CC","CC","DL","DL","TJ","TJ","CC","DL"],
    "客户":     ["CUST001","CUST002","CUST003","CUST001","CUST003","CUST002","CUST003","CUST001","CUST002"],
    "SKU":      ["SKU001"] * 9,
    "预测量":   [15, 8, 6, 12, 20, 10, 6, 9, 14],
    "修正后":   [13, 7, 5, 10, 16,  9, 5, 8, 12],
    "要求周":   ["第24周","第24周","第25周","第24周","第25周","第24周","第25周","第25周","第25周"],
})

with tab1:
    st.subheader("选择进入优化的预测")

    # ── filters ──────────────────────────────────────────────────────────────
    fc1, fc2 = st.columns([2, 3])
    with fc1:
        week_options = sorted(_MOCK_FORECASTS["要求周"].unique().tolist())
        selected_week = st.selectbox("要求周", ["全部"] + week_options)
    with fc2:
        dest_options = sorted(_MOCK_FORECASTS["目的地"].unique().tolist())
        selected_dests = st.multiselect("目的地筛选", dest_options, default=dest_options)

    if "optimized_ids" not in st.session_state:
        st.session_state.optimized_ids = set()

    pool = _MOCK_FORECASTS[~_MOCK_FORECASTS["预测编号"].isin(st.session_state.optimized_ids)].copy()

    filtered = pool.copy()
    if selected_week != "全部":
        filtered = filtered[filtered["要求周"] == selected_week]
    if selected_dests:
        filtered = filtered[filtered["目的地"].isin(selected_dests)]

    if filtered.empty:
        st.success("当前筛选范围内无待优化预测")
    else:
        st.caption("勾选要加入优化池的预测行（可多选）")
        selection = st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
        )

        selected_rows = selection.selection.rows
        n_selected = len(selected_rows)

        if n_selected:
            st.info(f"已选 **{n_selected}** 条预测进入优化池")
            if st.button("🚀 运行优化", type="primary"):
                ids_to_mark = filtered.iloc[selected_rows]["预测编号"].tolist()
                st.session_state.optimized_ids.update(ids_to_mark)
                st.success(f"优化完成，{len(ids_to_mark)} 条预测已标记完成，请查看「优化结果」标签页")
                st.rerun()
        else:
            st.button("🚀 运行优化", type="primary", disabled=True)
            st.caption("请先勾选至少一条预测")

with tab2:
    st.subheader("优化结果 — 推荐方案")
    st.dataframe({
        "计划编号": ["PLN0001", "PLN0002", "PLN0003"],
        "目的地": ["CC", "DL", "TJ"],
        "SKU": ["SKU001", "SKU001", "SKU001"],
        "类型": ["预置", "预置", "预置"],
        "托盘数": [30, 22, 24],
        "运输方式": ["公路/车辆", "公路/车辆", "公路/车辆"],
        "资源编号": ["V0001", "V0006", "V0011"],
        "运费": ["¥12,000", "¥10,000", "¥8,000"],
        "装载率": ["85%", "78%", "80%"],
    }, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("装载方案可视化")
    st.info("车辆装载率计算结果")
    st.dataframe({
        "运输方式": ["公路/车辆", "公路/车辆", "公路/车辆"],
        "资源编号": ["V0001", "V0006", "V0011"],
        "车型": ["40尺箱式集装箱", "40尺箱式集装箱", "40尺箱式集装箱"],
        "最大托盘": [36, 36, 36],
        "实际装载": [30, 22, 24],
        "装载率": ["83.3%", "61.1%", "66.7%"],
    }, use_container_width=True, hide_index=True)
