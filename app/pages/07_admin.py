"""Page 7: System Administration — x value, confidence, safety stock, loading config."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.engines.loading_calculator import (
    VEHICLE_SPECS, PALLET_SPECS, calculate_loading, calculate_all_combinations,
    get_loading_rate,
)
from src.database.models import LoadingConfig

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "supply_chain.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

# Ensure the table exists and rows are seeded (safe for upgrades from older DBs)
from src.database.models import Base
Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables["loading_config"]])
from src.database.seed_data import seed_loading_config as _seed_lc
_s = Session()
try:
    _seed_lc(_s)
finally:
    _s.close()

VEHICLE_LABELS = {
    "40ft_container": "40尺箱式集装箱",
    "semi_trailer": "半挂栏板车",
}
PALLET_LABELS = {
    "EUR_1200x800": "欧标托盘 1200×800",
    "JP_1100x1100": "日标托盘 1100×1100",
}

st.set_page_config(page_title="系统管理", page_icon="⚙️", layout="wide")
st.title("⚙️ 系统管理")
st.caption("交付时效目标(x)、预测置信度、安全库存参数配置")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "x值配置", "置信度管理", "安全库存参数", "车辆资源", "运价维护", "装载率配置",
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
        "来源": ["人工设置", "人工设置", "人工设置", "人工设置", "人工设置"],
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
        "车型": ["40尺箱式集装箱", "40尺箱式集装箱", "半挂栏板车", "半挂栏板车"],
        "承运商": ["CR001", "CR001", "CR002", "CR002"],
        "限重(kg)": [26000, 26000, 30000, 30000],
        "状态": ["可用", "可用", "可用", "已锁定"],
    }, use_container_width=True, hide_index=True)

with tab5:
    st.subheader("运价维护")
    st.dataframe({
        "运价ID": ["FR0001", "FR0002", "FR0003"],
        "承运商": ["CR001", "CR001", "CR002"],
        "目的地": ["CC", "DL", "TJ"],
        "计价模式": ["按车计价", "按车计价", "按车计价"],
        "单价": [12000, 10000, 8000],
        "紧急附加": [1.0, 1.5, 1.0],
    }, use_container_width=True, hide_index=True)

with tab6:
    st.subheader("装载率配置")
    st.caption("系统根据托盘尺寸与车辆尺寸自动计算理论最大装载量；管理员可确认或覆盖实际可用容量")

    # Load current confirmed values from DB
    session = Session()
    try:
        configs = {(c.vehicle_type, c.pallet_type): c for c in session.query(LoadingConfig).all()}
    finally:
        session.close()

    # Summary table
    st.subheader("标准组合一览")
    rows = []
    for r in calculate_all_combinations():
        cfg = configs.get((r.vehicle_type, r.pallet_type))
        confirmed = cfg.confirmed_max if cfg and cfg.confirmed_max is not None else "—"
        effective = cfg.confirmed_max if cfg and cfg.confirmed_max is not None else r.max_pallets
        rows.append({
            "车型": VEHICLE_LABELS.get(r.vehicle_type, r.vehicle_type),
            "托盘规格": PALLET_LABELS.get(r.pallet_type, r.pallet_type),
            "理论最大(托)": r.max_pallets,
            "管理员确认(托)": confirmed,
            "实际生效(托)": effective,
            "叠放层数": r.layers,
            "每层数量": r.pallets_per_layer,
            "装载方案": r.arrangement_description,
            "备注": cfg.notes if cfg else "",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("管理员确认 / 覆盖")
    st.info("当特殊货物或包装质量与标准不同时，管理员可在此覆盖系统计算值")

    col1, col2 = st.columns(2)
    with col1:
        sel_vehicle = st.selectbox(
            "车型",
            list(VEHICLE_SPECS.keys()),
            format_func=lambda k: VEHICLE_LABELS.get(k, k),
        )
    with col2:
        sel_pallet = st.selectbox(
            "托盘规格",
            list(PALLET_SPECS.keys()),
            format_func=lambda k: PALLET_LABELS.get(k, k),
        )

    calc = calculate_loading(VEHICLE_SPECS[sel_vehicle], PALLET_SPECS[sel_pallet])
    existing = configs.get((sel_vehicle, sel_pallet))

    c1, c2, c3 = st.columns(3)
    c1.metric("系统计算最大值(托)", calc.max_pallets)
    c2.metric(
        "当前确认值(托)",
        existing.confirmed_max if existing and existing.confirmed_max is not None else "未设置",
    )
    c3.metric(
        "确认人",
        existing.confirmed_by if existing and existing.confirmed_by else "—",
    )

    with st.form("override_loading"):
        override_val = st.number_input(
            "覆盖最大装载量(托)",
            min_value=0,
            max_value=calc.theoretical_max,
            value=existing.confirmed_max if existing and existing.confirmed_max is not None else calc.max_pallets,
            help="填0表示清除覆盖，恢复系统计算值",
        )
        notes_val = st.text_area(
            "备注",
            value=existing.notes or "",
            placeholder="例：该客户产品包装较松，实测每层只能放16托",
        )
        confirmed_by_val = st.text_input(
            "操作人",
            value=existing.confirmed_by or "",
            placeholder="填写工号或姓名",
        )
        submitted = st.form_submit_button("💾 保存确认值", type="primary")

    if submitted:
        session = Session()
        try:
            cfg = session.query(LoadingConfig).filter_by(
                vehicle_type=sel_vehicle, pallet_type=sel_pallet
            ).first()
            if cfg is None:
                cfg = LoadingConfig(
                    vehicle_type=sel_vehicle,
                    pallet_type=sel_pallet,
                    theoretical_max=calc.max_pallets,
                )
                session.add(cfg)
            cfg.theoretical_max = calc.max_pallets
            cfg.confirmed_max = override_val if override_val > 0 else None
            cfg.notes = notes_val or None
            cfg.confirmed_by = confirmed_by_val or None
            cfg.confirmed_at = datetime.now()
            session.commit()
            st.success(
                f"已保存：{VEHICLE_LABELS.get(sel_vehicle, sel_vehicle)} + "
                f"{PALLET_LABELS.get(sel_pallet, sel_pallet)} → "
                f"生效值 {override_val if override_val > 0 else calc.max_pallets} 托"
            )
            st.rerun()
        except Exception as e:
            session.rollback()
            st.error(f"保存失败：{e}")
        finally:
            session.close()

    st.markdown("---")
    st.subheader("自定义装载率计算")
    col3, col4, col5 = st.columns(3)
    with col3:
        calc_vehicle = st.selectbox(
            "车型 ", list(VEHICLE_SPECS.keys()),
            format_func=lambda k: VEHICLE_LABELS.get(k, k),
            key="calc_v",
        )
    with col4:
        calc_pallet = st.selectbox(
            "托盘规格 ", list(PALLET_SPECS.keys()),
            format_func=lambda k: PALLET_LABELS.get(k, k),
            key="calc_p",
        )
    with col5:
        _preview = calculate_loading(VEHICLE_SPECS[calc_vehicle], PALLET_SPECS[calc_pallet])
        actual_qty = st.number_input(
            "实际发运量(托)", min_value=0, max_value=_preview.theoretical_max,
            value=min(20, _preview.theoretical_max),
        )

    result = calculate_loading(VEHICLE_SPECS[calc_vehicle], PALLET_SPECS[calc_pallet], actual_pallets=actual_qty)
    # Apply admin confirmed_max if set — override the system-calculated ceiling
    _calc_cfg = configs.get((calc_vehicle, calc_pallet))
    effective_max = (
        _calc_cfg.confirmed_max
        if _calc_cfg and _calc_cfg.confirmed_max is not None
        else result.max_pallets
    )
    effective_rate = round(actual_qty / effective_max * 100, 1) if effective_max > 0 else 0.0
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("有效最大容量(托)", effective_max,
              help="已有管理员确认值时显示确认值，否则显示系统计算值")
    m2.metric("实际发运(托)", actual_qty)
    m3.metric("装载率", f"{effective_rate}%")
    m4.metric("约束因素", "体积" if result.volume_limited <= result.weight_limited else "重量")
    if actual_qty > effective_max:
        st.warning(f"⚠️ 实际发运量 {actual_qty} 超过有效最大容量 {effective_max}，装载率超过 100%")
    if _calc_cfg and _calc_cfg.confirmed_max is not None and _calc_cfg.confirmed_max != result.max_pallets:
        st.info(f"ℹ️ 管理员确认值 {_calc_cfg.confirmed_max} 托（系统计算值 {result.max_pallets} 托）")
    st.info(f"装载方案: {result.arrangement_description}")
