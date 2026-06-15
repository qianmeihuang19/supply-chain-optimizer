"""SQLAlchemy ORM models — 25 tables for supply chain optimizer v3.2."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# =============================================================================
# 13 Base Data Tables
# =============================================================================


class Shipper(Base):
    __tablename__ = "shippers"

    shipper_id = Column(String(20), primary_key=True)
    shipper_name = Column(String(50), nullable=False)
    contact = Column(String(50), nullable=True)


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(20), primary_key=True)
    customer_name = Column(String(50), nullable=False)
    contact = Column(String(50), nullable=True)


class Destination(Base):
    __tablename__ = "destinations"

    dest_id = Column(String(10), primary_key=True)
    dest_name = Column(String(50), nullable=False)
    transit_days_normal = Column(Integer, nullable=False)
    transit_days_winter = Column(Integer, nullable=False)
    local_delivery_days = Column(Float, nullable=False, default=1.0)


class DeliveryTarget(Base):
    __tablename__ = "delivery_targets"

    target_id = Column(String(20), primary_key=True)
    customer_id = Column(String(20), nullable=True)   # NULL = global default
    dest_id = Column(String(10), ForeignKey("destinations.dest_id"), nullable=True)
    target_days_x = Column(Integer, nullable=False)
    priority = Column(Integer, nullable=False, default=10)


class Carrier(Base):
    __tablename__ = "carriers"

    carrier_id = Column(String(20), primary_key=True)
    carrier_name = Column(String(50), nullable=False)
    carrier_type = Column(String(20), nullable=False, default="公路")   # 公路 / 水路 / 铁路
    contact = Column(String(50), nullable=True)


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(String(20), primary_key=True)
    vehicle_type = Column(String(30), nullable=False)     # "40ft_container", "semi_trailer"
    carrier_id = Column(String(20), nullable=False)
    max_weight_kg = Column(Float, nullable=False)
    inner_length_mm = Column(Float, nullable=False)
    inner_width_mm = Column(Float, nullable=False)
    max_height_mm = Column(Float, nullable=False)
    available_from = Column(Date, nullable=False)
    available_to = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="available")


class FreightRate(Base):
    __tablename__ = "freight_rates"

    rate_id = Column(String(20), primary_key=True)
    carrier_id = Column(String(20), nullable=False)
    origin = Column(String(10), nullable=False)
    destination = Column(String(10), ForeignKey("destinations.dest_id"), nullable=False)
    pricing_mode = Column(String(20), nullable=False)    # per_vehicle / per_ton / per_pallet
    unit_price = Column(Float, nullable=False)
    min_charge = Column(Float, nullable=False, default=0)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=False)
    vehicle_type = Column(String(30), nullable=False)
    is_express = Column(Boolean, nullable=False, default=False)
    express_surcharge = Column(Float, nullable=False, default=1.0)


class PackagingSpec(Base):
    __tablename__ = "packaging_specs"

    pallet_type = Column(String(30), primary_key=True)
    pallet_length_mm = Column(Float, nullable=False)
    pallet_width_mm = Column(Float, nullable=False)
    pallet_height_mm = Column(Float, nullable=False)
    pallet_weight_kg = Column(Float, nullable=False)
    stackable_layers = Column(Integer, nullable=False, default=1)
    gap_mm = Column(Float, nullable=False, default=50)


class PenaltyRule(Base):
    __tablename__ = "penalty_rules"

    rule_id = Column(String(20), primary_key=True)
    customer_id = Column(String(20), nullable=False)
    penalty_type = Column(String(20), nullable=False)    # linear / tiered
    linear_rate = Column(Float, nullable=False, default=0)
    tier_rules = Column(JSON, nullable=True)             # [{"days_from":1,"days_to":3,"rate":150}, ...]


class ForecastConfidence(Base):
    __tablename__ = "forecast_confidence"

    confidence_id = Column(String(20), primary_key=True)
    customer_id = Column(String(20), nullable=True)
    dest_id = Column(String(10), ForeignKey("destinations.dest_id"), nullable=True)
    confidence_value = Column(Float, nullable=False, default=0.80)
    source = Column(String(20), nullable=False, default="manual")
    manual_override = Column(Float, nullable=True)
    system_suggested = Column(Float, nullable=True)
    bias_direction = Column(Float, nullable=True)         # signed float: +0.15 = over-reports by 15%, -0.10 = under-reports by 10%
    bias_correction = Column(Float, nullable=True)
    sample_size = Column(Integer, nullable=True, default=0)
    last_updated = Column(DateTime, nullable=True)


class SafetyStockParam(Base):
    __tablename__ = "safety_stock_params"

    param_id = Column(String(20), primary_key=True)
    dest_id = Column(String(10), ForeignKey("destinations.dest_id"), nullable=False)
    service_level_z = Column(Float, nullable=False, default=1.65)
    demand_std_sigma = Column(Float, nullable=False, default=3.0)
    replenishment_lead_days = Column(Float, nullable=False, default=5.0)
    calculated_safety_stock = Column(Float, nullable=False, default=0.0)
    manual_override = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=True)


class TransferRoute(Base):
    __tablename__ = "transfer_routes"

    from_dest = Column(String(10), ForeignKey("destinations.dest_id"), primary_key=True)
    to_dest = Column(String(10), ForeignKey("destinations.dest_id"), primary_key=True)
    transfer_days = Column(Integer, nullable=False)
    transfer_cost_per_pallet = Column(Float, nullable=False)
    min_transfer_qty = Column(Integer, nullable=False, default=1)
    is_return_route = Column(Boolean, nullable=False, default=False)


class ReturnParam(Base):
    __tablename__ = "return_params"

    dest_id = Column(String(10), ForeignKey("destinations.dest_id"), primary_key=True)
    return_freight_per_pallet = Column(Float, nullable=False)
    return_transit_days = Column(Integer, nullable=False)
    return_handling_cost = Column(Float, nullable=False)
    backhaul_discount = Column(Float, nullable=False, default=0.0)


class TerminalCapability(Base):
    __tablename__ = "terminal_capabilities"

    dest_id = Column(String(10), ForeignKey("destinations.dest_id"), primary_key=True)
    daily_handling_capacity = Column(Integer, nullable=False)
    storage_capacity = Column(Integer, nullable=False)
    storage_cost_unit = Column(String(30), nullable=False, default="元/托盘/天")
    storage_cost_rate = Column(Float, nullable=False)
    local_delivery_cost_per_pallet = Column(Float, nullable=False)
    local_delivery_coverage_km = Column(Float, nullable=False)


class CargoValueParam(Base):
    __tablename__ = "cargo_value_params"

    sku_id = Column(String(20), primary_key=True)
    unit_value_per_pallet = Column(Float, nullable=False)
    damage_rate_per_handling = Column(Float, nullable=False, default=0.5)
    time_decay_rate = Column(Float, nullable=False, default=0.1)
    shelf_life_days = Column(Integer, nullable=True)
    secondary_transfer_penalty = Column(Float, nullable=False, default=1.3)


class TerminalDemandProbability(Base):
    __tablename__ = "terminal_demand_probability"

    dest_id = Column(String(10), ForeignKey("destinations.dest_id"), primary_key=True)
    forecast_window_days = Column(Integer, primary_key=True, default=14)
    demand_probability = Column(Float, nullable=False)
    expected_quantity = Column(Integer, nullable=False)
    last_updated = Column(DateTime, nullable=True)
    data_source = Column(String(30), nullable=True)


# =============================================================================
# 7 Business Data Tables
# =============================================================================


class SalesForecast(Base):
    __tablename__ = "sales_forecasts"

    forecast_id = Column(String(20), primary_key=True)
    shipper_id = Column(String(20), ForeignKey("shippers.shipper_id"), nullable=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), nullable=False)
    destination = Column(String(10), ForeignKey("destinations.dest_id"), nullable=False)
    sku_id = Column(String(20), ForeignKey("cargo_value_params.sku_id"), nullable=True)
    quantity_pallets = Column(Integer, nullable=False)
    adjusted_quantity = Column(Integer, nullable=False)
    required_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    batch_id = Column(String(20), nullable=True)
    confidence_at_time = Column(Float, nullable=True)


class ShipmentPlan(Base):
    __tablename__ = "shipment_plans"

    plan_id = Column(String(20), primary_key=True)
    batch_id = Column(String(20), nullable=False)
    destination = Column(String(10), ForeignKey("destinations.dest_id"), nullable=False)
    plan_type = Column(String(20), nullable=False)       # preposition / responsive / emergency
    transport_mode = Column(String(30), nullable=False, default="公路/车辆")  # 公路/车辆 / 水路 / 铁路
    planned_ship_date = Column(Date, nullable=False)
    planned_arrival_date = Column(Date, nullable=False)
    quantity_pallets = Column(Integer, nullable=False)
    preposition_quantity = Column(Integer, nullable=False, default=0)
    safety_stock_quantity = Column(Integer, nullable=False, default=0)
    resource_id = Column(String(20), nullable=True)      # vehicle / vessel / wagon ID
    carrier_id = Column(String(20), ForeignKey("carriers.carrier_id"), nullable=True)
    freight_cost = Column(Float, nullable=False, default=0)
    penalty_cost = Column(Float, nullable=False, default=0)
    storage_cost = Column(Float, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0)
    loading_rate = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="draft")


class ShipmentPlanItem(Base):
    """Per-shipper/customer cargo breakdown within a shipment plan."""
    __tablename__ = "shipment_plan_items"

    item_id = Column(String(20), primary_key=True)
    plan_id = Column(String(20), ForeignKey("shipment_plans.plan_id"), nullable=False)
    shipper_id = Column(String(20), ForeignKey("shippers.shipper_id"), nullable=False)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), nullable=False)
    sku_id = Column(String(20), ForeignKey("cargo_value_params.sku_id"), nullable=True)
    quantity_pallets = Column(Integer, nullable=False)


class OrderConfirmation(Base):
    __tablename__ = "order_confirmations"

    confirm_id = Column(String(20), primary_key=True)
    forecast_id = Column(String(20), ForeignKey("sales_forecasts.forecast_id"), nullable=False)
    shipper_id = Column(String(20), ForeignKey("shippers.shipper_id"), nullable=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), nullable=True)
    sku_id = Column(String(20), ForeignKey("cargo_value_params.sku_id"), nullable=True)
    confirmed_quantity = Column(Integer, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_delivery_date = Column(Date, nullable=True)
    confirmed_by = Column(String(30), nullable=True)
    delta_quantity = Column(Integer, nullable=True)
    delta_vs_adjusted = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    alarm_triggered_at = Column(DateTime, nullable=True)
    confirmed_notes = Column(Text, nullable=True)


class ForecastDeviationLog(Base):
    __tablename__ = "forecast_deviation_log"

    log_id = Column(String(20), primary_key=True)
    forecast_id = Column(String(20), ForeignKey("sales_forecasts.forecast_id"), nullable=False)
    customer_id = Column(String(20), nullable=False)
    dest_id = Column(String(10), ForeignKey("destinations.dest_id"), nullable=False)
    forecast_qty = Column(Integer, nullable=False)
    confirmed_qty = Column(Integer, nullable=False)
    deviation_pct = Column(Float, nullable=False)
    deviation_direction = Column(String(10), nullable=False)  # over/under/exact/cancelled
    order_size_tier = Column(String(10), nullable=False)       # small/medium/large
    period_tag = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class Waybill(Base):
    __tablename__ = "waybills"

    waybill_id = Column(String(20), primary_key=True)
    plan_id = Column(String(20), ForeignKey("shipment_plans.plan_id"), nullable=False)
    actual_ship_time = Column(DateTime, nullable=True)
    eta = Column(DateTime, nullable=True)
    ata = Column(DateTime, nullable=True)
    eta_deviation_hours = Column(Float, nullable=True)


class TerminalInventory(Base):
    __tablename__ = "terminal_inventory"

    dest_id = Column(String(10), ForeignKey("destinations.dest_id"), primary_key=True)
    current_stock = Column(Integer, nullable=False, default=0)
    safety_stock = Column(Integer, nullable=False, default=0)
    prepositioned_stock = Column(Integer, nullable=False, default=0)
    confirmed_pending_delivery = Column(Integer, nullable=False, default=0)
    surplus_stock = Column(Integer, nullable=False, default=0)
    awaiting_confirmation = Column(Integer, nullable=False, default=0)
    in_transit_arriving_tomorrow = Column(Integer, nullable=False, default=0)
    storage_days = Column(Integer, nullable=False, default=0)


class TransferPlan(Base):
    __tablename__ = "transfer_plans"

    transfer_id = Column(String(20), primary_key=True)
    from_dest = Column(String(10), ForeignKey("destinations.dest_id"), nullable=False)
    to_dest = Column(String(10), ForeignKey("destinations.dest_id"), nullable=False)
    quantity_pallets = Column(Integer, nullable=False)
    transfer_cost = Column(Float, nullable=False, default=0)
    return_quantity = Column(Integer, nullable=False, default=0)
    return_cost = Column(Float, nullable=False, default=0)
    storage_cost_saved = Column(Float, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="planned")


class LoadingConfig(Base):
    """Admin-confirmed loading capacities, overriding the system calculation."""
    __tablename__ = "loading_config"

    vehicle_type = Column(String(30), primary_key=True)
    pallet_type = Column(String(30), primary_key=True)
    theoretical_max = Column(Integer, nullable=False)   # system-calculated
    confirmed_max = Column(Integer, nullable=True)      # admin override; None = use theoretical
    notes = Column(Text, nullable=True)
    confirmed_by = Column(String(30), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
