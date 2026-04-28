"""Page 5: Order Confirmation Alarm Management (system staff page)."""
import streamlit as st

st.set_page_config(page_title="订单确认告警管理", page_icon="🚨", layout="wide")
st.title("🚨 订单确认告警管理")
st.caption("到货即检查 · 人工确认 · 告警追踪")

tab1, tab2, tab3 = st.tabs(["待处理告警", "人工确认", "确认历史"])

with tab1:
    st.subheader("待处理告警（到货时客户未确认）")
    st.error("🔴 以下订单货物已到达终端，但客户尚未确认订单")

    alerts = [
        {"预警": "HIGH", "预测编号": "F0012", "客户": "CUST001", "终端": "长春(CC)",
         "到达时间": "2025-04-20 08:00", "预置量": "15托盘", "已等待": "2天"},
        {"预警": "HIGH", "预测编号": "F0015", "客户": "CUST003", "终端": "大连(DL)",
         "到达时间": "2025-04-19 08:00", "预置量": "12托盘", "已等待": "3天"},
    ]
    for a in alerts:
        with st.container(border=True):
            cols = st.columns([1, 2, 1, 1, 1])
            with cols[0]:
                st.error(f"🔴 {a['预警']}")
            with cols[1]:
                st.write(f"**{a['预测编号']}** | {a['客户']} → {a['终端']}")
                st.write(f"到达: {a['到达时间']} | 预置: {a['预置量']}")
            with cols[2]:
                st.write(f"已等待: {a['已等待']}")
            with cols[3]:
                st.button("联系客户", key=f"contact_{a['预测编号']}")
            with cols[4]:
                st.button("人工确认", key=f"confirm_{a['预测编号']}", type="primary")

with tab2:
    st.subheader("人工确认表单")
    with st.form("manual_confirm"):
        st.text_input("预测编号", placeholder="F0012")
        st.number_input("确认数量(托盘)", min_value=0, max_value=100, value=15)
        st.selectbox("确认来源", ["口头确认", "邮件确认", "电话确认", "系统建议"])
        st.text_area("备注说明", placeholder="请填写决策依据，如：客户电话确认，需求15托")
        st.form_submit_button("✅ 确认", type="primary")

with tab3:
    st.subheader("确认历史记录")
    st.dataframe({
        "预测编号": ["F0008", "F0005"],
        "终端": ["长春", "天津"],
        "确认方式": ["客户确认", "人工确认"],
        "确认时间": ["2025-04-18 14:30", "2025-04-17 09:00"],
        "确认量": [10, 18],
        "响应时间": ["1天", "0.5天"],
    }, use_container_width=True, hide_index=True)

    st.subheader("性能指标")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("平均告警响应时间", "1.2天")
        st.metric("告警处理中", "2笔")
    with c2:
        st.metric("人工确认占比", "35%")
        st.metric("本周告警数", "8笔")
