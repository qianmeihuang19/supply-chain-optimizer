"""Seed realistic demo data for all 20 tables.

Rules from supply_chain_plan.md section 8:
- Forecasts: 3 destinations x 5-10 orders/day, 3-20 pallets (Poisson), due +7-14 days
- Month-end +30%, Spring Festival -50%
- Confirmation deviation: 70% exact, 15% decrease 10-50%, 10% increase 10-30%, 5% cancelled
- ETA deviation: N(0,4h) normal, N(6h,8h) winter, 5% extreme delay 12-48h
"""
from __future__ import annotations

import math
import random
from datetime import date, datetime, timedelta
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from .models import (
    CargoValueParam,
    DeliveryTarget,
    Destination,
    ForecastConfidence,
    ForecastDeviationLog,
    FreightRate,
    LoadingConfig,
    OrderConfirmation,
    PackagingSpec,
    PenaltyRule,
    ReturnParam,
    SafetyStockParam,
    SalesForecast,
    ShipmentPlan,
    TerminalCapability,
    TerminalDemandProbability,
    TerminalInventory,
    TransferPlan,
    TransferRoute,
    Vehicle,
    Waybill,
)

# --- Config ---
CUSTOMER_IDS = ["CUST001", "CUST002", "CUST003"]
CARRIER_IDS = ["CR001", "CR002"]
DEST_CODES = ["CC", "DL", "TJ"]
DEST_NAMES = {"CC": "长春", "DL": "大连", "TJ": "天津"}
SKU_ID = "SKU001"
BASE_DATE = date(2025, 4, 1)   # simulation start
SIM_DAYS = 60                   # 2 months of history
SPRING_FESTIVAL_MONTHS = {1, 2}

# Seed RNG
rng = np.random.default_rng(42)
py_rng = random.Random(42)


def _id(prefix: str, seq: int) -> str:
    return f"{prefix}{seq:04d}"


def _rand_date_range(start: date, days: int) -> date:
    return start + timedelta(days=int(rng.integers(0, days)))


def _is_month_end(d: date) -> bool:
    return d.day >= 28


def _daily_order_count(d: date) -> int:
    """5-10 orders per destination, +30% month-end, -50% spring festival."""
    base = int(rng.integers(5, 11))
    if _is_month_end(d):
        base = int(base * 1.3)
    if d.month in SPRING_FESTIVAL_MONTHS:
        base = max(2, int(base * 0.5))
    return base


# =============================================================================
# Seed functions for each table
# =============================================================================


def seed_destinations(session: Session):
    data = [
        ("CC", "长春", 4, 5, 1.0),
        ("DL", "大连", 3, 4, 1.0),
        ("TJ", "天津", 2, 3, 1.0),
    ]
    for row in data:
        session.add(Destination(
            dest_id=row[0], dest_name=row[1],
            transit_days_normal=row[2], transit_days_winter=row[3],
            local_delivery_days=row[4],
        ))
    session.commit()


def seed_delivery_targets(session: Session):
    # Global default x=2, plus per-destination overrides
    seq = 1
    # global default
    session.add(DeliveryTarget(
        target_id=_id("DT", seq), customer_id=None, dest_id=None,
        target_days_x=2, priority=100,
    ))
    seq += 1
    for dest in DEST_CODES:
        session.add(DeliveryTarget(
            target_id=_id("DT", seq), customer_id=None, dest_id=dest,
            target_days_x=2, priority=50,
        ))
        seq += 1
    # CUST001 wants faster delivery to CC
    session.add(DeliveryTarget(
        target_id=_id("DT", seq), customer_id="CUST001", dest_id="CC",
        target_days_x=1, priority=10,
    ))
    session.commit()


def seed_vehicles(session: Session):
    """Generate ~20 vehicles across two carriers."""
    spec = {
        "40ft_container": (26000, 12032, 2352, 2690),
        "semi_trailer": (30000, 13600, 2440, 2800),
    }
    seq = 1
    for carrier in CARRIER_IDS:
        for vtype, dims in spec.items():
            for _ in range(5):
                session.add(Vehicle(
                    vehicle_id=_id("V", seq),
                    vehicle_type=vtype,
                    carrier_id=carrier,
                    max_weight_kg=dims[0],
                    inner_length_mm=dims[1],
                    inner_width_mm=dims[2],
                    max_height_mm=dims[3],
                    available_from=BASE_DATE,
                    available_to=BASE_DATE + timedelta(days=SIM_DAYS + 30),
                    status="available",
                ))
                seq += 1
    session.commit()


def seed_freight_rates(session: Session):
    """Generate freight rates per carrier x destination x vehicle type."""
    base_rates = {"CC": 12000, "DL": 10000, "TJ": 8000}
    seq = 1
    for carrier in CARRIER_IDS:
        for dest, base in base_rates.items():
            for vtype in ["40ft_container", "semi_trailer"]:
                # normal rate
                session.add(FreightRate(
                    rate_id=_id("FR", seq), carrier_id=carrier,
                    origin="SH", destination=dest,
                    pricing_mode="per_vehicle",
                    unit_price=base, min_charge=int(base * 0.8),
                    valid_from=BASE_DATE, valid_to=BASE_DATE + timedelta(days=365),
                    vehicle_type=vtype, is_express=False, express_surcharge=1.0,
                ))
                seq += 1
                # express rate
                session.add(FreightRate(
                    rate_id=_id("FR", seq), carrier_id=carrier,
                    origin="SH", destination=dest,
                    pricing_mode="per_vehicle",
                    unit_price=base, min_charge=int(base * 0.8),
                    valid_from=BASE_DATE, valid_to=BASE_DATE + timedelta(days=365),
                    vehicle_type=vtype, is_express=True, express_surcharge=1.5,
                ))
                seq += 1
    session.commit()


def seed_packaging_specs(session: Session):
    specs = [
        ("EUR_1200x800", 1200, 800, 1200, 600, 2, 50),
        ("JP_1100x1100", 1100, 1100, 1100, 550, 2, 50),
    ]
    for row in specs:
        session.add(PackagingSpec(
            pallet_type=row[0], pallet_length_mm=row[1], pallet_width_mm=row[2],
            pallet_height_mm=row[3], pallet_weight_kg=row[4],
            stackable_layers=row[5], gap_mm=row[6],
        ))
    session.commit()


def seed_penalty_rules(session: Session):
    for cust in CUSTOMER_IDS:
        session.add(PenaltyRule(
            rule_id=_id("PR", CUSTOMER_IDS.index(cust) + 1),
            customer_id=cust,
            penalty_type="linear",
            linear_rate=200.0,
            tier_rules=None,
        ))
    session.commit()


def seed_forecast_confidence(session: Session):
    """Initial manual confidence values."""
    seq = 1
    for cust in CUSTOMER_IDS:
        for dest in DEST_CODES:
            conf = 0.75 + py_rng.random() * 0.15  # 0.75-0.90
            session.add(ForecastConfidence(
                confidence_id=_id("FC", seq),
                customer_id=cust, dest_id=dest,
                confidence_value=round(conf, 2),
                source="manual",
                manual_override=round(conf, 2),
                system_suggested=None,
                bias_direction=None,
                bias_correction=None,
                sample_size=0,
                last_updated=datetime.now(),
            ))
            seq += 1
    session.commit()


def seed_safety_stock_params(session: Session):
    from ..utils.helpers import calc_safety_stock
    for dest in DEST_CODES:
        z = 1.65
        sigma = 3.0
        L = {"CC": 5.0, "DL": 4.0, "TJ": 3.0}[dest]
        ss = calc_safety_stock(z, sigma, L)
        session.add(SafetyStockParam(
            param_id=_id("SS", DEST_CODES.index(dest) + 1),
            dest_id=dest,
            service_level_z=z,
            demand_std_sigma=sigma,
            replenishment_lead_days=L,
            calculated_safety_stock=round(ss, 2),
            last_updated=datetime.now(),
        ))
    session.commit()


def seed_transfer_routes(session: Session):
    """6 inter-terminal routes only. Return-to-origin logistics is handled by return_params."""
    costs = {
        ("CC", "DL"): (1, 80, 5),
        ("CC", "TJ"): (2, 100, 5),
        ("DL", "CC"): (1, 80, 5),
        ("DL", "TJ"): (1, 60, 5),
        ("TJ", "CC"): (2, 100, 5),
        ("TJ", "DL"): (1, 60, 5),
    }
    for (f, t), (days, cost, min_q) in costs.items():
        session.add(TransferRoute(
            from_dest=f, to_dest=t,
            transfer_days=days, transfer_cost_per_pallet=cost,
            min_transfer_qty=min_q, is_return_route=False,
        ))
    session.commit()


def seed_return_params(session: Session):
    params = {"CC": (150, 4, 50, 0.6), "DL": (130, 3, 50, 0.6), "TJ": (100, 2, 50, 0.6)}
    for dest, (freight, days, handling, discount) in params.items():
        session.add(ReturnParam(
            dest_id=dest,
            return_freight_per_pallet=freight,
            return_transit_days=days,
            return_handling_cost=handling,
            backhaul_discount=discount,
        ))
    session.commit()


def seed_terminal_capabilities(session: Session):
    caps = {
        "CC": (80, 500, 15.0, 30, 50),
        "DL": (60, 400, 12.0, 28, 45),
        "TJ": (70, 450, 14.0, 25, 40),
    }
    for dest, (cap, store, rate, delivery, cover) in caps.items():
        session.add(TerminalCapability(
            dest_id=dest,
            daily_handling_capacity=cap,
            storage_capacity=store,
            storage_cost_unit="元/托盘/天",
            storage_cost_rate=rate,
            local_delivery_cost_per_pallet=delivery,
            local_delivery_coverage_km=cover,
        ))
    session.commit()


def seed_cargo_value_params(session: Session):
    session.add(CargoValueParam(
        sku_id=SKU_ID,
        unit_value_per_pallet=20000.0,
        damage_rate_per_handling=0.005,   # 0.5% per handling as fraction
        time_decay_rate=0.001,            # 0.1%/day as fraction
        shelf_life_days=None,
        secondary_transfer_penalty=1.3,
    ))
    session.commit()


def seed_terminal_demand_probability(session: Session):
    seq = 0
    for dest in DEST_CODES:
        prob = {"CC": 0.65, "DL": 0.60, "TJ": 0.70}[dest]
        exp = {"CC": 15, "DL": 12, "TJ": 18}[dest]
        session.add(TerminalDemandProbability(
            dest_id=dest,
            forecast_window_days=14,
            demand_probability=prob,
            expected_quantity=exp,
            last_updated=datetime.now(),
            data_source="historical_frequency",
        ))
        seq += 1
    session.commit()


# --- Business data seeding ---


def seed_sales_forecasts(session: Session) -> list[dict]:
    """Generate SIM_DAYS of forecast data and return order records for downstream tables."""
    from ..utils.helpers import get_transit_days
    from .models import ForecastConfidence

    # Build (customer_id, dest_id) -> confidence_value lookup from seeded table
    conf_rows = session.query(ForecastConfidence).all()
    conf_lookup = {(r.customer_id, r.dest_id): r.confidence_value for r in conf_rows}

    records = []
    seq = 1
    for day_offset in range(SIM_DAYS):
        current_date = BASE_DATE + timedelta(days=day_offset)
        for dest in DEST_CODES:
            n_orders = _daily_order_count(current_date)
            for _ in range(n_orders):
                customer = py_rng.choice(CUSTOMER_IDS)
                qty = int(rng.poisson(10)) + 3   # mean ~10, offset +3 => ~3-20
                qty = max(3, min(qty, 20))
                # due date: +7 to +14 days
                due = current_date + timedelta(days=int(rng.integers(7, 15)))
                created = datetime.combine(current_date, datetime.min.time().replace(
                    hour=8, minute=int(rng.integers(0, 60))
                ))

                # snapshot confidence: customer+dest → dest-level → global (None,None) → hardcoded default
                conf = conf_lookup.get(
                    (customer, dest),
                    conf_lookup.get(
                        (None, dest),
                        conf_lookup.get((None, None), 0.80),
                    ),
                )
                # adjusted quantity
                adjusted = max(1, int(qty * conf))

                rec = dict(
                    forecast_id=_id("F", seq),
                    customer_id=customer,
                    destination=dest,
                    quantity_pallets=qty,
                    adjusted_quantity=adjusted,
                    required_date=due,
                    date_precision="day",
                    created_at=created,
                    batch_id=None,
                    confidence_at_time=conf,
                )
                records.append(rec)
                session.add(SalesForecast(**rec))
                seq += 1
    session.commit()
    return records


def seed_order_confirmations(session: Session, forecasts: list[dict]):
    """Generate order confirmations with realistic deviation patterns."""
    from ..utils.helpers import get_transit_days

    # Systematic bias: CUST001 tends to over-forecast by 15%
    CUSTOMER_BIAS = {"CUST001": 1.15, "CUST002": 1.0, "CUST003": 0.90}

    records = []
    seq = 1
    for rec in forecasts:
        qty = rec["quantity_pallets"]
        cust = rec["customer_id"]

        # deviation logic
        r = py_rng.random()
        if r < 0.70:
            # exact match
            confirmed_qty = qty
            direction = "exact"
        elif r < 0.85:
            # decrease 10-50%
            factor = 1.0 - py_rng.uniform(0.10, 0.50)
            confirmed_qty = max(1, int(qty * factor))
            direction = "under"
        elif r < 0.95:
            # increase 10-30%
            factor = 1.0 + py_rng.uniform(0.10, 0.30)
            confirmed_qty = int(qty * factor)
            direction = "over"
        else:
            # cancelled
            confirmed_qty = 0
            direction = "cancelled"

        # apply systematic bias
        if cust in CUSTOMER_BIAS and confirmed_qty > 0:
            confirmed_qty = max(1, int(confirmed_qty * CUSTOMER_BIAS[cust]))

        # decide who confirmed and when
        # shipment arrives after transit + some lead
        dest = rec["destination"]
        transit = get_transit_days(dest, rec["required_date"])
        ship_date = rec["required_date"] - timedelta(days=transit + 2)
        arrival_date = ship_date + timedelta(days=transit)

        # customer can confirm before, at, or after arrival
        confirm_offset = py_rng.choice([-2, -1, 0, 1, 2, 3])
        confirm_date = arrival_date + timedelta(days=confirm_offset)
        confirm_dt = datetime.combine(confirm_date, datetime.min.time().replace(hour=10))

        if confirm_offset >= 0 and py_rng.random() < 0.3:
            # Cargo arrived but customer has not yet confirmed — alarm triggered, awaiting resolution
            status = "arrival_alarm"
            confirmed_by = None
            alarm_dt = datetime.combine(arrival_date, datetime.min.time().replace(hour=8))
            confirmed_at = None   # not yet confirmed; confirmed_at set only on resolution
        else:
            status = "customer_confirmed"
            confirmed_by = f"CUST_{cust}"
            alarm_dt = None
            confirmed_at = confirm_dt

        delta = confirmed_qty - qty
        delta_adj = confirmed_qty - rec["adjusted_quantity"]

        size_tier = "small" if confirmed_qty <= 5 else ("medium" if confirmed_qty <= 15 else "large")

        oc = dict(
            confirm_id=_id("OC", seq),
            forecast_id=rec["forecast_id"],
            confirmed_quantity=confirmed_qty,
            confirmed_at=confirmed_at,
            confirmed_delivery_date=rec["required_date"],
            confirmed_by=confirmed_by,
            delta_quantity=delta,
            delta_vs_adjusted=delta_adj,
            status=status,
            alarm_triggered_at=alarm_dt,
            confirmed_notes=None,
        )
        records.append(oc)
        session.add(OrderConfirmation(**oc))
        seq += 1
    session.commit()
    return records


def seed_forecast_deviation_log(session: Session, forecasts: list[dict], confirmations: list[dict]):
    """Log deviations for finalized confirmations only (excludes unresolved arrival_alarm rows)."""
    conf_map = {c["forecast_id"]: c for c in confirmations}

    records = []
    seq = 1
    for rec in forecasts[:500]:  # limit for performance
        fc = conf_map.get(rec["forecast_id"])
        if fc is None:
            continue
        # Skip unresolved alarms — they are not yet finalized forecast outcomes
        if fc["status"] == "arrival_alarm":
            continue
        if fc["confirmed_quantity"] == 0:
            direction = "cancelled"
        elif fc["confirmed_quantity"] > rec["quantity_pallets"]:
            direction = "over"
        elif fc["confirmed_quantity"] < rec["quantity_pallets"]:
            direction = "under"
        else:
            direction = "exact"

        dev_pct = 0.0
        if rec["quantity_pallets"] > 0:
            dev_pct = round(
                (fc["confirmed_quantity"] - rec["quantity_pallets"]) / rec["quantity_pallets"] * 100, 1
            )

        tier = fc["confirmed_quantity"] or 0
        size_tier = "small" if tier <= 5 else ("medium" if tier <= 15 else "large")

        period_tag = "month_end" if rec["required_date"].day >= 28 else "normal"
        if rec["required_date"].month in SPRING_FESTIVAL_MONTHS:
            period_tag = "holiday"

        log_rec = dict(
            log_id=_id("DL", seq),
            forecast_id=rec["forecast_id"],
            customer_id=rec["customer_id"],
            dest_id=rec["destination"],
            forecast_qty=rec["quantity_pallets"],
            confirmed_qty=fc["confirmed_quantity"],
            deviation_pct=dev_pct,
            deviation_direction=direction,
            order_size_tier=size_tier,
            period_tag=period_tag,
            created_at=datetime.now(),
        )
        records.append(log_rec)
        session.add(ForecastDeviationLog(**log_rec))
        seq += 1
    session.commit()


def seed_terminal_inventory(session: Session):
    """Initial zeroed inventory for each terminal."""
    for dest in DEST_CODES:
        ss = {"CC": 12, "DL": 10, "TJ": 8}[dest]
        session.add(TerminalInventory(
            dest_id=dest,
            current_stock=ss,
            safety_stock=ss,
            prepositioned_stock=0,
            confirmed_pending_delivery=0,
            surplus_stock=0,
            awaiting_confirmation=0,
            in_transit_arriving_tomorrow=0,
            storage_days=0,
        ))
    session.commit()


def seed_loading_config(session: Session):
    """Seed loading_config with system-calculated values (no confirmed overrides)."""
    from src.engines.loading_calculator import VEHICLE_SPECS, PALLET_SPECS, calculate_loading
    for vehicle in VEHICLE_SPECS.values():
        for pallet in PALLET_SPECS.values():
            existing = session.query(LoadingConfig).filter_by(
                vehicle_type=vehicle.vehicle_type, pallet_type=pallet.pallet_type
            ).first()
            if existing is None:
                result = calculate_loading(vehicle, pallet)
                session.add(LoadingConfig(
                    vehicle_type=vehicle.vehicle_type,
                    pallet_type=pallet.pallet_type,
                    theoretical_max=result.max_pallets,
                    confirmed_max=None,
                    notes=None,
                    confirmed_by=None,
                    confirmed_at=None,
                ))
    session.commit()


def seed_all(session: Session, simulate: bool = True) -> dict:
    """Seed all tables. Returns a summary dict.

    Args:
        session: SQLAlchemy session.
        simulate: If True, also generate business data (forecasts, confirmations, etc.).
    """
    # Base data (13 tables)
    seed_destinations(session)
    seed_delivery_targets(session)
    seed_vehicles(session)
    seed_freight_rates(session)
    seed_packaging_specs(session)
    seed_penalty_rules(session)
    seed_forecast_confidence(session)
    seed_safety_stock_params(session)
    seed_transfer_routes(session)
    seed_return_params(session)
    seed_terminal_capabilities(session)
    seed_cargo_value_params(session)
    seed_terminal_demand_probability(session)
    seed_loading_config(session)

    summary = {
        "destinations": 3,
        "delivery_targets": 5,
        "vehicles": 20,
        "freight_rates": 24,
        "packaging_specs": 2,
        "penalty_rules": 3,
        "forecast_confidence": 9,
        "safety_stock_params": 3,
        "transfer_routes": 6,
        "return_params": 3,
        "terminal_capabilities": 3,
        "cargo_value_params": 1,
        "terminal_demand_probability": 3,
        "loading_config": 4,
    }

    if simulate:
        forecasts = seed_sales_forecasts(session)
        confirmations = seed_order_confirmations(session, forecasts)
        seed_forecast_deviation_log(session, forecasts, confirmations)
        seed_terminal_inventory(session)
        summary["sales_forecasts"] = len(forecasts)
        summary["order_confirmations"] = len(confirmations)

    return summary
