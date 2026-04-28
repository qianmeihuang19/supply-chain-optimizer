# 供应链计划优化系统 (Supply Chain Planning Optimizer) v3.2

基于数学优化(MIP)的供应链发货计划与终端调拨双引擎优化系统。

## 核心特性
- 可配置的目标交付天数x（控制预置库存深度）
- 预测置信度分层管理（EWMA自动更新）
- 动态安全库存（Z×σ×√L公式）
- 订单确认与货物到达并行处理（到货即检查+告警机制）
- 滚动补货策略（高置信→验证→响应式→紧急）
- 三条闭环反馈（预测偏差/ETA偏差/终端滞留）

## 快速开始

```bash
pip install -r requirements.txt
python -m src.database.init_db
python -m src.database.seed_data
uvicorn src.api.routes:app --reload --port 8000
streamlit run app/app.py  # 新终端窗口
```

## 文档
- CLAUDE.md — Claude Code 项目指令
- docs/supply_chain_plan.md — 完整项目计划(v3.2)
