# Capillary 开发进度追踪

最后更新：2026-06-14

---

## Phase 0 — 基础设施 ✅ 完成

**git commit**: `a34deb1` Phase 0: infrastructure — ORM models, DB init, seed data, Streamlit framework
**后续修复**: `7b5b665` Fix 6 Phase 0 bugs found in Codex review

完成内容：
- 项目目录结构
- SQLAlchemy ORM 数据模型（`src/database/models.py`）：20张表
- 数据库初始化（`src/database/init_db.py`）
- 模拟数据生成（`src/database/seed_data.py`，612行）
- Streamlit 8个页面框架（`app/pages/01~08`）
  - **07_admin.py（268行）**：唯一接真实数据库的页面，6个配置 tab（x值/置信度/安全库存/装载配置/车辆/路线）
  - **其余7个页面**：均为 UI 骨架 + 硬编码假数据，`st.info("此处显示...")` 占位，不连 DB，无业务逻辑

---

## Phase 1 — 装载率计算 ✅ 完成

**git commit**: `4df0b9e` Phase 1: loading rate calculator with tests and admin UI
**后续改进**: `7ebec20` Apply 6 fixes from Codex review; `1e3f7fc` Phase 1 improvements: Chinese UI and admin loading config override

完成内容：
- 装载率计算引擎（`src/engines/loading_calculator.py`）
  - 托盘装箱（间隙/叠放/限重/限高）
  - 多车型支持（40ft箱式集装箱 + 半挂栏板车）
- 单元测试（`tests/test_loading_calculator.py`）
- Admin UI 中文化 + 装载配置覆盖

---

## Phase 2 — 引擎一：发货计划 MIP ⏳ 待开发

**优先级**：🔴 最高（参赛核心卖点）

待创建文件：
- `src/engines/shipment_optimizer.py` — 主体MIP，OR-Tools 求解
- `src/engines/preposition_calculator.py` — 预置深度 + 安全库存计算
- `src/engines/confidence_engine.py` — 置信度 EWMA 更新
- `tests/test_shipment_optimizer.py`
- `tests/test_preposition.py`
- `tests/test_confidence.py`

核心要点（来自 CLAUDE.md）：
- 目标：Min(运费 + 违约 + 存储 + 资金占用 + 安全库存持有 - 装载率奖励)
- 决策变量：x_ship[i,v,t]（托盘数整数）+ y_use[i,v,t]（是否用车 0/1）
- 11条约束（详见 `04_Code/supply-chain-optimizer/CLAUDE.md`）
- 滚动补货：批1高置信60% → 批2验证30% → 批3响应10% → 紧急1.5x

---

## Phase 3 — 资源锁定 ⏳ 待开发

待创建文件：
- `src/services/batch_manager.py`
- `src/services/resource_locker.py`
- `src/services/waybill_service.py`

---

## Phase 4 — ETA + 偏差反馈 ⏳ 待开发

待创建文件：
- `src/engines/eta_predictor.py`
- `src/services/inventory_service.py`
- `tests/test_confidence.py`（含ETA偏差→σ更新）

---

## Phase 5 — 订单确认 + 引擎二 ⏳ 待开发

待创建文件：
- `src/services/order_confirm_service.py` — 到货检查 + 告警
- `src/engines/transfer_optimizer.py` — 调拨MIP，OR-Tools 求解
- `src/services/cost_calculator.py`
- `tests/test_transfer_optimizer.py`
- `tests/test_order_confirm.py`
- `tests/test_cost_calculator.py`

核心要点（引擎二）：
- 目标：Min(调拨成本×(1+二次惩罚) + 退货+处置费 + 存储×天数 + 货损衰减 - 避免违约收益)
- 决策变量：t[i,j]调拨 + r[i]退货 + s[i]存储 + b[i,j]回程(0/1)
- 9条约束（详见 `04_Code/supply-chain-optimizer/CLAUDE.md`）

---

## Phase 6 — 仪表板 ⏳ 待开发

- `app/pages/01_dashboard.py`（当前为空壳）：KPI 仪表板
- `app/pages/08_analytics.py`（当前为空壳）：预测准确率趋势

---

## Phase 7 — 集成测试 + Demo 准备 ⏳ 待开发

- 端到端测试：模拟数据 → 引擎一 → 运单 → 到货 → 引擎二
- Demo 脚本准备（见 `03_Diagrams/Scenarios Presentation/`）
- 演讲稿 PPT 最终版

---

## 当前状态核查（2026-06-14）

| 文件 | 行数 | 真实状态 |
|------|------|----------|
| `src/database/models.py` | 312 | ✅ 20张表完整 |
| `src/database/seed_data.py` | 612 | ✅ 含泊松分布/季节性数据 |
| `src/engines/loading_calculator.py` | 210 | ✅ Phase 1 核心逻辑 |
| `tests/test_loading_calculator.py` | 196 | ✅ 单元测试 |
| `app/pages/07_admin.py` | 268 | ✅ 接真实DB |
| `app/pages/01~06,08` | 39–65 各 | ⚠️ 仅UI骨架，假数据 |
| `src/engines/shipment_optimizer.py` | — | ❌ 文件不存在 |
| `src/engines/transfer_optimizer.py` | — | ❌ 文件不存在 |
| `src/services/*.py`（6个） | 1各 | ❌ 全部空文件 |
| `src/api/routes.py` | 1 | ❌ 空文件 |

---

## 风险与注意事项

- **头号风险**：双引擎 MIP 一行未写，初赛截止 2027-01-31，时间紧张
- 所有优化模型的目标函数和约束必须与 `CLAUDE.md` 数学定义严格一致
- OR-Tools 求解器：使用 `from ortools.sat.python import cp_model` 或 `ortools.linear_solver`
- 专利申报：5个候选方向已列明，路演前须递交（见 `Capillary_专利申报建议书.docx`）
