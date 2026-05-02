"""Page 7: System Administration — x value, confidence, safety stock, etc."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from src.engines.loading_calculator import (
    VEHICLE_SPECS, PALLET_SPECS, calculate_loading, calculate_all_combinations, get_loading_rate,
)

st.set_page_config(page_title="系统管理", page_icon="⚙️", layout="wide")
st.title("⚙️ 系统管理")
st.caption("交付时效目标(x)、预测置信度、安全库存参数配置")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "x值配置", "置信度管理", "安全库存参数", "车辆资源", "运价维护", "装载率计算",
])

with tab1:
    st.subheader("交付时效目标 x 配置")
    st.info("x定义从订单确认到货物送达的最大天数，按客户×目的地独立配置")
    st.dataframe({
        "配置ID": ["DT0001", "DT0002", "DT0003", "DT0004", "DT0005"],
        "客户": ["全局", "全局", "全局", "CUST001", "全局"],
        "目的地": ["全局", "CC", "DL", "CC", "TJ"],
        "x值": [2, 2, 2, 1, 2],
        "优先级": [100, 50, 50, 10, 50],
    }, use_container_width=True, hide_index=True)

    with st.form("update_x"):
        cols = st.columns(3)
        with cols[0]:
            st.selectbox("客户", ["全局", "CUST001", "CUST002", "CUST003"])
        with cols[1]:
            st.selectbox("目的地", ["全局", "CC", "DL", "TJ"])
        with cols[2]:
            st.number_input("x值(天)", min_value=1, max_value=7, value=2)
        st.form_submit_button("更新配置")

with tab2:
    st.subheader("预测置信度管理")
    st.info("置信度范围: 0.40-0.95 | 人工值优先于系统建议值")
    st.dataframe({
        "客户": ["CUST001", "CUST001", "CUST002", "CUST002", "CUST003"],
        "目的地": ["CC", "DL", "CC", "DL", "CC"],
        "当前置信度": [0.85, 0.82, 0.80, 0.78, 0.88],
        "来源": ["manual", "manual", "manual", "manual", "manual"],
        "系统建议": ["—", "—", "—", "—", "—"],
        "样本数": [0, 0, 0, 0, 0],
    }, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("安全库存参数 Z / σ / L")
    st.dataframe({
        "终端": ["CC-长春", "DL-大连", "TJ-天津"],
        "服务水平Z": [1.65, 1.65, 1.65],
        "需求σ(托盘/天)": [3.0, 3.0, 3.0],
        "补货提前期L(天)": [5.0, 4.0, 3.0],
        "安全库存(托盘)": ["11.07", "9.90", "8.57"],
    }, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("车辆资源池")
    st.dataframe({
        "车辆ID": ["V0001", "V0002", "V0006", "V0007"],
        "车型": ["40ft_container", "40ft_container", "semi_trailer", "semi_trailer"],
        "承运商": ["CR001", "CR001", "CR002", "CR002"],
        "限重(kg)": [26000, 26000, 30000, 30000],
        "状态": ["available", "available", "available", "locked"],
    }, use_container_width=True, hide_index=True)

with tab5:
    st.subheader("运价维护")
    st.dataframe({
        "运价ID": ["FR0001", "FR0002", "FR0003"],
        "承运商": ["CR001", "CR001", "CR002"],
        "目的地": ["CC", "DL", "TJ"],
        "计价模式": ["per_vehicle", "per_vehicle", "per_vehicle"],
        "单价": [12000, 10000, 8000],
        "紧急附加": [1.0, 1.5, 1.0],
    }, use_container_width=True, hide_index=True)

with tab6:
    st.subheader("装载率计算")
    st.caption("基于托盘尺寸 × 车辆尺寸 × 限重限高，自动计算最大装载量")

    st.subheader("标准组合一览")
    rows = []
    for r in calculate_all_combinations():
        rows.append({
            "车型": r.vehicle_type,
            "托盘规格": r.pallet_type,
            "最大装载(托)": r.max_pallets,
            "体积限制(托)": r.volume_limited,
            "重量限制(托)": r.weight_limited,
            "叠放层数": r.layers,
            "每层数量": r.pallets_per_layer,
            "装载方案": r.arrangement_description,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("自定义装载率计算")
    col1, col2, col3 = st.columns(3)
    with col1:
        sel_vehicle = st.selectbox("车型", list(VEHICLE_SPECS.keys()))
    with col2:
        sel_pallet = st.selectbox("托盘规格", list(PALLET_SPECS.keys()))
    with col3:
        # compute max first so we can cap the input
        _preview = calculate_loading(VEHICLE_SPECS[sel_vehicle], PALLET_SPECS[sel_pallet])
        actual_qty = st.number_input(
            "实际发运量(托)", min_value=0, max_value=_preview.theoretical_max, value=min(20, _preview.theoretical_max)
        )

    result = calculate_loading(VEHICLE_SPECS[sel_vehicle], PALLET_SPECS[sel_pallet], actual_pallets=actual_qty)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最大容量(托)", result.max_pallets)
    c2.metric("实际发运(托)", actual_qty)
    c3.metric("装载率", f"{result.loading_rate_pct}%")
    c4.metric("约束因素", "体积" if result.volume_limited <= result.weight_limited else "重量")
    if actual_qty > result.max_pallets:
        st.warning(f"⚠️ 实际发运量 {actual_qty} 超过最大容量 {result.max_pallets}，装载率超过 100%")
    st.info(f"装载方案: {result.arrangement_description}")
