"""Page 2: Sales Forecast Management."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import SalesForecast, OrderConfirmation

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "supply_chain.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

DEST_OPTIONS = {"CC-长春": "CC", "DL-大连": "DL", "TJ-天津": "TJ"}
CUSTOMERS = ["CUST001", "CUST002", "CUST003"]

st.set_page_config(page_title="销售预测管理", page_icon="📈", layout="wide")
st.title("📈 销售预测管理")
st.caption("预测录入、置信度修正、订单确认")

tab1, tab2, tab3 = st.tabs(["预测录入", "预测列表", "订单确认"])

with tab1:
    st.subheader("新增销售预测")

    with st.form("new_forecast"):
        col1, col2, col3 = st.columns(3)
        with col1:
            customer = st.selectbox("客户", CUSTOMERS)
        with col2:
            dest_label = st.selectbox("目的地", list(DEST_OPTIONS.keys()))
        with col3:
            qty = st.number_input("预测数量(托盘)", min_value=1, max_value=100, value=10)

        today = date.today()
        wcol1, wcol2 = st.columns(2)
        with wcol1:
            year = st.number_input("要求交付年份", min_value=2025, max_value=2030,
                                   value=today.year, step=1)
        with wcol2:
            max_week = date(int(year), 12, 28).isocalendar()[1]
            cur_week = today.isocalendar()[1]
            week_num = st.number_input("要求交付周（ISO周）", min_value=1,
                                       max_value=int(max_week),
                                       value=int(cur_week), step=1)
        due = date.fromisocalendar(int(year), int(week_num), 3)
        st.caption(f"实际存储日期：**{due}**（第 {week_num} 周周三）")

        submitted = st.form_submit_button("提交预测")
        if submitted:
            st.success(f"预测已提交: {qty}托盘 → {dest_label}, 第 {week_num} 周（{due}）")

with tab2:
    st.subheader("已提交预测列表")
    st.info("此处显示已录入的销售预测及置信度修正后数量")
    st.dataframe(
        {
            "预测编号": ["F0001", "F0002", "F0003"],
            "客户": ["CUST001", "CUST002", "CUST003"],
            "目的地": ["CC", "DL", "TJ"],
            "预测量": [15, 8, 20],
            "修正后": [13, 8, 17],
            "置信度": [0.85, 0.80, 0.82],
            "要求日期": ["2025-04-28", "2025-04-30", "2025-05-01"],
        },
        use_container_width=True, hide_index=True,
    )

with tab3:
    st.subheader("订单确认")
    st.caption("选择客户、目的地和交付周，系统查询匹配预测后逐条确认")

    # ── 查询条件（表单外，驱动查询）────────────────────────────────
    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
    with qcol1:
        q_customer = st.selectbox("客户", CUSTOMERS, key="q_cust")
    with qcol2:
        q_dest_label = st.selectbox("目的地", list(DEST_OPTIONS.keys()), key="q_dest")
    with qcol3:
        q_year = st.number_input("年份", min_value=2025, max_value=2030,
                                 value=date.today().year, step=1, key="q_year")
    with qcol4:
        q_max_week = date(int(q_year), 12, 28).isocalendar()[1]
        q_cur_week = date.today().isocalendar()[1]
        q_week = st.number_input("交付周（ISO周）", min_value=1,
                                 max_value=int(q_max_week),
                                 value=int(q_cur_week), step=1, key="q_week")

    q_dest = DEST_OPTIONS[q_dest_label]
    q_due = date.fromisocalendar(int(q_year), int(q_week), 3)
    st.caption(f"查询条件：{q_customer} → {q_dest_label}，第 {q_week} 周（{q_due}）")

    # ── 查询数据库 ──────────────────────────────────────────────────
    session = Session()
    forecasts = (
        session.query(SalesForecast)
        .filter(
            SalesForecast.customer_id == q_customer,
            SalesForecast.destination == q_dest,
            SalesForecast.required_date == q_due,
        )
        .all()
    )
    confirmed_ids = {
        oc.forecast_id
        for oc in session.query(OrderConfirmation.forecast_id)
        .filter(
            OrderConfirmation.forecast_id.in_([f.forecast_id for f in forecasts]),
            OrderConfirmation.status.in_(["customer_confirmed", "manual_confirmed"]),
        )
        .all()
    }
    session.close()

    # ── 显示结果 ────────────────────────────────────────────────────
    if not forecasts:
        st.warning("未找到匹配的预测记录，请确认客户、目的地和交付周是否正确。")
    else:
        st.write(f"共找到 **{len(forecasts)}** 条预测记录：")
        for fc in forecasts:
            already = fc.forecast_id in confirmed_ids
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 3])
                with c1:
                    st.write(f"**{fc.forecast_id}**")
                with c2:
                    st.write(f"预测量：{fc.quantity_pallets} 托盘")
                with c3:
                    st.write(f"修正后：{fc.adjusted_quantity} 托盘")
                with c4:
                    if already:
                        st.success("已确认")
                    else:
                        with st.form(f"confirm_{fc.forecast_id}"):
                            conf_qty = st.number_input(
                                "确认数量(托盘)",
                                min_value=0, max_value=200,
                                value=fc.adjusted_quantity,
                                key=f"qty_{fc.forecast_id}",
                            )
                            if st.form_submit_button("确认"):
                                st.success(f"{fc.forecast_id} 已确认：{conf_qty} 托盘")
