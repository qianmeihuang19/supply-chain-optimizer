"""Loading rate calculator — pallet arrangement in vehicles.

Computes max pallets per vehicle considering:
- Pallet footprint (length × width) with gap between pallets
- Stacking layers up to height limit
- Weight limit
- Two vehicle types: 40ft container and semi-trailer
- Two pallet types: EUR 1200×800 and JP 1100×1100
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class PalletSpec:
    pallet_type: str
    length_mm: float
    width_mm: float
    height_mm: float
    weight_kg: float
    stackable_layers: int
    gap_mm: float = 50.0


@dataclass
class VehicleSpec:
    vehicle_type: str
    inner_length_mm: float
    inner_width_mm: float
    max_height_mm: float
    max_weight_kg: float


@dataclass
class LoadingResult:
    vehicle_type: str
    pallet_type: str
    max_pallets: int
    volume_limited: int
    weight_limited: int
    loading_rate_pct: float        # actual / theoretical_max × 100
    theoretical_max: int
    layers: int
    pallets_per_layer: int
    arrangement_description: str


# Default specs from seed data / CLAUDE.md
VEHICLE_SPECS: dict[str, VehicleSpec] = {
    "40ft_container": VehicleSpec(
        vehicle_type="40ft_container",
        inner_length_mm=12032,
        inner_width_mm=2352,
        max_height_mm=2690,
        max_weight_kg=26000,
    ),
    "semi_trailer": VehicleSpec(
        vehicle_type="semi_trailer",
        inner_length_mm=13600,
        inner_width_mm=2440,
        max_height_mm=2800,
        max_weight_kg=30000,
    ),
}

PALLET_SPECS: dict[str, PalletSpec] = {
    "EUR_1200x800": PalletSpec(
        pallet_type="EUR_1200x800",
        length_mm=1200,
        width_mm=800,
        height_mm=1200,
        weight_kg=600,
        stackable_layers=2,
        gap_mm=50,
    ),
    "JP_1100x1100": PalletSpec(
        pallet_type="JP_1100x1100",
        length_mm=1100,
        width_mm=1100,
        height_mm=1100,
        weight_kg=550,
        stackable_layers=2,
        gap_mm=50,
    ),
}


def _pallets_per_layer(vehicle: VehicleSpec, pallet: PalletSpec) -> tuple[int, str]:
    """Return (count, description) of pallets fitting in one floor layer.

    Tries both pallet orientations and picks the better one.
    Gap is added between pallets but not at the walls (pallets can touch walls).
    """
    gap = pallet.gap_mm

    def fit_1d(space: float, unit: float) -> int:
        if unit <= 0:
            return 0
        # first pallet fits without leading gap; each subsequent needs +gap
        n = 1
        used = unit
        while used + gap + unit <= space:
            used += gap + unit
            n += 1
        return n

    # Orientation A: pallet length along vehicle length
    cols_a = fit_1d(vehicle.inner_length_mm, pallet.length_mm)
    rows_a = fit_1d(vehicle.inner_width_mm, pallet.width_mm)
    count_a = cols_a * rows_a

    # Orientation B: pallet rotated 90° (width along vehicle length)
    cols_b = fit_1d(vehicle.inner_length_mm, pallet.width_mm)
    rows_b = fit_1d(vehicle.inner_width_mm, pallet.length_mm)
    count_b = cols_b * rows_b

    if count_a >= count_b:
        return count_a, f"{cols_a}列×{rows_a}行(朝向A)"
    return count_b, f"{cols_b}列×{rows_b}行(朝向B)"


def calculate_loading(
    vehicle: VehicleSpec,
    pallet: PalletSpec,
    actual_pallets: Optional[int] = None,
) -> LoadingResult:
    """Calculate loading capacity and rate for a vehicle + pallet combination.

    Args:
        vehicle: Vehicle dimensions and weight limit.
        pallet: Pallet dimensions, weight, and stacking spec.
        actual_pallets: If provided, compute loading_rate_pct against this instead of max.
    """
    # Max stacking layers limited by vehicle height
    stacked_height = pallet.height_mm * pallet.stackable_layers
    max_layers_by_height = max(1, int(vehicle.max_height_mm // pallet.height_mm))
    layers = min(pallet.stackable_layers, max_layers_by_height)

    per_layer, arrangement_desc = _pallets_per_layer(vehicle, pallet)
    volume_limited = per_layer * layers

    # Weight limit
    weight_limited = int(vehicle.max_weight_kg // pallet.weight_kg)

    max_pallets = min(volume_limited, weight_limited)

    # Theoretical max ignores weight (pure geometry)
    theoretical_max = volume_limited

    ref = actual_pallets if actual_pallets is not None else max_pallets
    loading_rate_pct = round(ref / theoretical_max * 100, 1) if theoretical_max > 0 else 0.0

    binding = "体积限制" if volume_limited <= weight_limited else "重量限制"
    description = (
        f"{arrangement_desc}, {layers}层叠放, "
        f"每层{per_layer}托, 共{max_pallets}托 ({binding})"
    )

    return LoadingResult(
        vehicle_type=vehicle.vehicle_type,
        pallet_type=pallet.pallet_type,
        max_pallets=max_pallets,
        volume_limited=volume_limited,
        weight_limited=weight_limited,
        loading_rate_pct=loading_rate_pct,
        theoretical_max=theoretical_max,
        layers=layers,
        pallets_per_layer=per_layer,
        arrangement_description=description,
    )


def calculate_all_combinations() -> list[LoadingResult]:
    """Return loading results for all vehicle × pallet combinations."""
    results = []
    for vehicle in VEHICLE_SPECS.values():
        for pallet in PALLET_SPECS.values():
            results.append(calculate_loading(vehicle, pallet))
    return results


def get_loading_rate(
    vehicle_type: str,
    pallet_type: str,
    actual_pallets: int,
) -> float:
    """Return loading_rate_pct for a given actual shipment quantity."""
    vehicle = VEHICLE_SPECS[vehicle_type]
    pallet = PALLET_SPECS[pallet_type]
    result = calculate_loading(vehicle, pallet, actual_pallets=actual_pallets)
    return result.loading_rate_pct
