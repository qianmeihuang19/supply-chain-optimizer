# CLAUDE.md — 供应链计划优化系统 v3.2

## 项目概述

构建基于数学优化(MIP)的供应链发货计划与终端调拨优化系统Demo。
- **预测驱动的库存预置**：基于销售预测+置信度修正，提前将货物布局到距终端x天交付距离内
- 双引擎架构：引擎一(发货计划优化) + 引擎二(终端调拨优化)
- 三条闭环反馈：预测偏差→置信度、ETA偏差→在途时间、终端滞留→发货量扣减
- 订单确认与货物到达是两条独立并行时间线，到货即检查+告警机制
- Python全栈：FastAPI + Streamlit + OR-Tools + SQLite
- 详细设计文档见 `docs/supply_chain_plan.md`

## 核心设计理念

### 目标交付天数x
参数x定义从客户订单确认到货物送达客户的最大天数，按客户×目的地独立配置。
```
预置提前量(天) = 干线在途时间 - (x - 本地配送时间)
预置提前量 > 0 → 需提前发货预置到终端
预置提前量 ≤ 0 → 不需预置，响应式发货即可
```

### 订单确认与货物到达：两条独立并行时间线
- 客户订单确认时间完全由客户自身需求决定，与货物是否到达终端无关
- 货物到达终端时，系统**立即检查**该订单是否已被客户确认
  - 已确认 → 直接进入差异分析和本地配送
  - 未确认 → **立即发起ALARM**给系统人员（不等超时）
- 系统人员在告警管理页面手动处理（联系客户或人工确认）
- 告警可自动解除（系统人员处理前客户自行确认了）

### 安全库存公式
安全库存 = Z × σ × √L
- Z：服务水平系数(90%→1.28, 95%→1.65, 99%→2.33)
- σ：需求波动标准差，基于历史预测偏差自动计算
- L：补货提前期(天) = 下单处理 + 干线在途 + 入库

## 业务场景(Demo)

- 1个发货点(上海) → 3个终端(长春/大连/天津)
- 公路运输，托盘非危险品，单一SKU
- 车型：40ft箱式集装箱 + 半挂栏板车
- 在途(4-11月): 长春4天, 大连3天, 天津2天; (12-3月): +1天
- 本地配送：统一1天
- 每目的地每天5-10订单，3-20托盘(泊松分布)

## 技术栈

- Python 3.11+, FastAPI, Streamlit, Google OR-Tools, SQLite, Pandas, Plotly

## 项目结构

```
supply-chain-optimizer/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── docs/
│   └── supply_chain_plan.md
├── src/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                 # SQLAlchemy ORM (25张表)
│   │   ├── init_db.py
│   │   └── seed_data.py
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── shipment_optimizer.py     # 引擎一：发货计划MIP
│   │   ├── transfer_optimizer.py     # 引擎二：终端调拨MIP
│   │   ├── loading_calculator.py     # 装载率计算
│   │   ├── preposition_calculator.py # 预置深度+安全库存计算
│   │   ├── confidence_engine.py      # 置信度EWMA更新
│   │   └── eta_predictor.py          # ETA预测
│   ├── services/
│   │   ├── __init__.py
│   │   ├── batch_manager.py          # 批次管理
│   │   ├── resource_locker.py        # 资源锁定
│   │   ├── waybill_service.py        # 运单管理
│   │   ├── inventory_service.py      # 库存管理
│   │   ├── order_confirm_service.py  # 订单确认+到货检查+告警
│   │   └── cost_calculator.py        # 成本计算
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── app/
│   ├── app.py
│   └── pages/
│       ├── 01_dashboard.py           # KPI仪表板
│       ├── 02_sales_forecast.py      # 销售预测管理
│       ├── 03_shipment_plan.py       # 发货计划工作台
│       ├── 04_waybill_tracking.py    # 运单跟踪
│       ├── 05_order_alarm.py         # 订单确认告警管理
│       ├── 06_terminal_transfer.py   # 终端库存与调拨
│       ├── 07_admin.py               # 系统管理(x/置信度/安全库存配置)
│       └── 08_analytics.py           # 分析报表(预测准确率趋势)
├── data/
│   ├── templates/
│   └── sample/
└── tests/
    ├── test_shipment_optimizer.py
    ├── test_transfer_optimizer.py
    ├── test_loading_calculator.py
    ├── test_preposition.py
    ├── test_confidence.py
    ├── test_order_confirm.py
    └── test_cost_calculator.py
```

## 数据库表一览 (25张)

详细字段见 docs/supply_chain_plan.md 第三章。

基础数据(管理员维护，16张):
- shippers: 货主/托运人(编码/名称/联系方式)
- customers: 客户/收货人(编码/名称/联系方式)
- carriers: 承运商/服务商(编码/名称/运输方式/联系方式)
- destinations: 目的地(编码/名称/在途天数正常+冬季/本地配送时间)
- delivery_targets: 交付时效目标(客户×目的地的x值,优先级匹配)
- vehicles: 车辆资源(车型/限重/内部尺寸/可用时间窗/状态)
- freight_rates: 运价(承运商/计价模式/单价/有效期/是否加急/附加费率)
- packaging_specs: 包装规格(托盘尺寸/重量/叠放层数/间隙)
- penalty_rules: 违约规则(线性rate/阶梯tier_rules JSON)
- forecast_confidence: 预测置信度(人工值/EWMA建议值/偏差方向float/修正系数/样本数)
- safety_stock_params: 安全库存参数(Z/σ/L/计算值Z×σ×√L)
- transfer_routes: 调拨路线(6路线运价/时间/最低量)
- return_params: 退货参数(运价/处置费/回程运费折扣率)
- terminal_capabilities: 终端能力(装卸量/存储容量/存储单价/本地配送费用)
- cargo_value_params: 货值损耗(货值/货损率0.5%/衰减率0.1%天/保质期/二次惩罚1.3x)
- terminal_demand_probability: 需求概率(预测窗口/概率/预期量)

业务数据(9张):
- sales_forecasts: 销售预测(货主/客户/SKU/目的地/数量/修正后数量/要求周周一/置信度快照)
- shipment_plans: 发货计划(批次/类型/运输方式/resource_id/carrier_id/各项费用/状态)，货主客户在items层
- shipment_plan_items: 发货计划明细(plan_id/货主/客户/SKU/托盘数)，支持拼车多货主
- order_confirmations: 订单确认(货主/客户/SKU/confirmed_at/status含arrival_alarm/alarm_triggered_at)
- forecast_deviation_log: 预测偏差记录(偏差率/方向over|under|exact|cancelled/规模分层/时段标签)
- waybills: 运单(发货时间/ETA/ATA/偏差小时)
- terminal_inventory: 终端库存(预置/已确认待配送/等待确认/剩余/安全库存)
- transfer_plans: 调拨计划(来源/目标/调拨量/退货量/存储量/各项成本/状态)
- loading_config: 装载配置(车型/托盘型/理论最大值/管理员确认值)

## 引擎一：发货计划优化

触发: 货物出发前
KPI: Min(运费 + 违约 + 存储 + 资金占用 + 安全库存持有 - 装载率奖励)

决策变量: x_ship[i,v,t](托盘数,整数), y_use[i,v,t](是否用车,0/1)

11条约束:
1. 库存就绪(与x联动): terminal_stock + arriving(x天内) >= demand × confidence
2. 需求满足: Σx_ship >= adjusted_demand
3. 车辆容量(体积)
4. 车辆容量(重量)
5. 车辆可用性
6. 运力匹配(每车每时段一个目的地)
7. 终端存储容量
8. 在途库存纳入
9. 安全库存: terminal_stock >= Z×σ×√L
10. 终端滞留反馈扣减
11. 滚动补货: 单批 <= demand × max_preposition_ratio

七类参数: ①交付时效(x/本地配送/紧急运输) ②置信度(值/修正/方向/上下限) ③安全库存(Z/σ/L) ④运力运价(车辆池/多模式/可靠性/回程) ⑤装载在途(装载率/季节/天气/追踪) ⑥库存成本(存储/衰减/滞留反馈) ⑦批次优先级(合并窗口/预置比例/优先级/分组)

滚动补货: 批次1(高置信60%) → 批次2(验证30%) → 批次3(响应式10%) → 紧急(1.5x费率)

## 引擎二：终端调拨优化

触发: 订单确认量 < 预置量
KPI: Min(调拨成本×(1+二次惩罚) + 退货×(1-折扣)+处置费 + 存储×天数 + 货损 + 衰减 - 避免违约收益)

决策变量: t[i,j]调拨, r[i]退货, s[i]存储, b[i,j]回程(0/1)

9条约束: ①库存平衡 ②需求匹配 ③存储容量 ④调拨时间窗(与x联动) ⑤最低调拨量 ⑥装卸能力(双向) ⑦保质期 ⑧回程运力 ⑨非负

六类参数: ①调拨(运价/时间/最低量/回程) ②退货(运价/处置费/折扣) ③存储(单价/容量/预计天数) ④需求(未交付量/截止日/违约/概率) ⑤损耗(货值/货损/衰减/保质期/二次惩罚) ⑥能力(装卸量/排队量)

## 闭环反馈

- 引擎二→引擎一: 终端滞留量→下批发货扣减
- 引擎二→客户: 生产计划调整建议
- 预测偏差→置信度+σ更新→预置量调整
- ETA偏差→在途时间+L更新→安全库存调整

## 到货告警机制

```python
def on_cargo_arrival(forecast_id):
    order = get_order_confirmation(forecast_id)
    if order.status == "customer_confirmed":
        trigger_merge_and_delivery(forecast_id)
    elif order.status == "pending":
        order.status = "arrival_alarm"
        order.alarm_triggered_at = now()
        send_alarm_to_system_user(forecast_id)
```
status流转: pending → arrival_alarm → customer_confirmed 或 manual_confirmed

## 模拟数据

预测: 3目的地×每天5-10订单，3-20托盘(泊松), 截止+7~14天, 月末+30%, 春节-50%
确认偏差: 70%无偏差, 15%减10-50%, 10%增10-30%, 5%取消, 部分客户系统性偏差
ETA偏差: 正常N(0,4h), 冬季N(6h,8h), 5%概率额外延迟12-48h

## 开发阶段

Phase 0: 基础设施 — 项目结构/建表(25张)/模拟数据/Streamlit框架
Phase 1: 装载率 — 托盘装箱(间隙/叠放/限重/限高/多车型)
Phase 2: 引擎一★ — 置信度修正+安全库存+预置深度+MIP+滚动补货+x敏感性分析
Phase 3: 资源锁定 — 运力匹配(含紧急通道)/运单/锁定
Phase 4: ETA+偏差反馈 — ETA预测/偏差统计/置信度更新/σ更新
Phase 5: 订单确认+引擎二 — 到货告警/人工确认/调拨MIP/闭环
Phase 6: 仪表板 — KPI/预测准确率/优化对比
Phase 7: 集成测试 — 端到端/Demo演示

## 编码规范

- 代码和注释英文，UI中文
- 每个引擎有独立单元测试
- 优化模型的目标函数和约束必须与本文档的数学定义严格一致
- 成本统一人民币(元)，日期datetime，时区Asia/Shanghai
- 数据库SQLAlchemy ORM
- API格式: {"success": bool, "data": ..., "message": str}
- Streamlit: st.set_page_config(layout="wide")
- 回程运费折扣率含义: 实际运费 = 正价 × (1 - 折扣率)
