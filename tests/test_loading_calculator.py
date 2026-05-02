"""Unit tests for loading_calculator.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.engines.loading_calculator import (
    PalletSpec,
    VehicleSpec,
    LoadingResult,
    VEHICLE_SPECS,
    PALLET_SPECS,
    calculate_loading,
    calculate_all_combinations,
    get_loading_rate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def eur_pallet() -> PalletSpec:
    return PALLET_SPECS["EUR_1200x800"]


def jp_pallet() -> PalletSpec:
    return PALLET_SPECS["JP_1100x1100"]


def container_40ft() -> VehicleSpec:
    return VEHICLE_SPECS["40ft_container"]


def semi_trailer() -> VehicleSpec:
    return VEHICLE_SPECS["semi_trailer"]


# ---------------------------------------------------------------------------
# 1. Expected capacity for standard combinations
# ---------------------------------------------------------------------------

class TestStandardCapacity:
    def test_40ft_eur_pallet_layers_2(self):
        result = calculate_loading(container_40ft(), eur_pallet())
        # 40ft 12032×2352mm, EUR 1200×800+50gap:
        # 9 cols (length) × 2 rows (width) = 18/layer × 2 layers = 36
        assert result.max_pallets == 36, (
            f"40ft+EUR: expected 36 pallets, got {result.max_pallets}"
        )
        assert result.layers == 2
        assert result.pallets_per_layer == 18

    def test_semi_trailer_eur_pallet(self):
        result = calculate_loading(semi_trailer(), eur_pallet())
        # Semi is longer and wider, should fit more than 40ft
        result_40ft = calculate_loading(container_40ft(), eur_pallet())
        assert result.max_pallets >= result_40ft.max_pallets

    def test_jp_pallet_40ft_exact_capacity(self):
        jp = calculate_loading(container_40ft(), jp_pallet())
        # 40ft 12032×2352mm, JP 1100×1100+50gap:
        # 10 cols (length) × 2 rows (width) = 20/layer × 2 layers = 40
        assert jp.max_pallets == 40
        assert jp.layers == 2
        assert jp.pallets_per_layer == 20

    def test_returns_loading_result_type(self):
        result = calculate_loading(container_40ft(), eur_pallet())
        assert isinstance(result, LoadingResult)


# ---------------------------------------------------------------------------
# 2. Binding constraint: volume vs weight
# ---------------------------------------------------------------------------

class TestBindingConstraint:
    def test_max_pallets_is_min_of_volume_and_weight(self):
        result = calculate_loading(container_40ft(), eur_pallet())
        assert result.max_pallets == min(result.volume_limited, result.weight_limited)

    def test_very_heavy_pallet_is_weight_limited(self):
        heavy = PalletSpec(
            pallet_type="heavy_test",
            length_mm=1200, width_mm=800, height_mm=1200,
            weight_kg=5000,   # extremely heavy
            stackable_layers=2, gap_mm=50,
        )
        result = calculate_loading(container_40ft(), heavy)
        assert result.weight_limited < result.volume_limited
        assert result.max_pallets == result.weight_limited

    def test_very_tall_pallet_limits_layers(self):
        tall = PalletSpec(
            pallet_type="tall_test",
            length_mm=1200, width_mm=800, height_mm=1400,
            weight_kg=300, stackable_layers=2, gap_mm=50,
        )
        result = calculate_loading(container_40ft(), tall)
        # 2 × 1400 = 2800 > 2690 (40ft height), so only 1 layer allowed
        assert result.layers == 1


# ---------------------------------------------------------------------------
# 3. Loading rate
# ---------------------------------------------------------------------------

class TestLoadingRate:
    def test_full_load_100_pct(self):
        result = calculate_loading(container_40ft(), eur_pallet())
        max_p = result.max_pallets
        rate = get_loading_rate("40ft_container", "EUR_1200x800", max_p)
        assert rate == 100.0

    def test_half_load_approx_50_pct(self):
        result = calculate_loading(container_40ft(), eur_pallet())
        half = result.theoretical_max // 2
        rate = get_loading_rate("40ft_container", "EUR_1200x800", half)
        assert 48.0 <= rate <= 52.0

    def test_zero_pallets_is_zero(self):
        rate = get_loading_rate("40ft_container", "EUR_1200x800", 0)
        assert rate == 0.0

    def test_loading_rate_in_result_equals_max(self):
        result = calculate_loading(container_40ft(), eur_pallet())
        # When actual_pallets not supplied, rate is based on max_pallets / theoretical_max
        expected = round(result.max_pallets / result.theoretical_max * 100, 1)
        assert result.loading_rate_pct == expected


# ---------------------------------------------------------------------------
# 4. All combinations
# ---------------------------------------------------------------------------

class TestAllCombinations:
    def test_returns_four_combinations(self):
        results = calculate_all_combinations()
        assert len(results) == 4  # 2 vehicles × 2 pallets

    def test_all_positive_capacity(self):
        for r in calculate_all_combinations():
            assert r.max_pallets > 0, f"{r.vehicle_type}+{r.pallet_type} has 0 capacity"


# ---------------------------------------------------------------------------
# 5. Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_single_layer_pallet(self):
        single_layer = PalletSpec(
            pallet_type="single_test",
            length_mm=1200, width_mm=800, height_mm=1200,
            weight_kg=600, stackable_layers=1, gap_mm=50,
        )
        result = calculate_loading(container_40ft(), single_layer)
        assert result.layers == 1
        # max_pallets should be half of 2-layer EUR
        eur_result = calculate_loading(container_40ft(), eur_pallet())
        assert result.volume_limited == eur_result.volume_limited // 2

    def test_arrangement_description_not_empty(self):
        result = calculate_loading(container_40ft(), eur_pallet())
        assert len(result.arrangement_description) > 0

    def test_custom_vehicle_spec(self):
        tiny_truck = VehicleSpec(
            vehicle_type="tiny",
            inner_length_mm=2500, inner_width_mm=1500,
            max_height_mm=1500, max_weight_kg=1000,
        )
        result = calculate_loading(tiny_truck, eur_pallet())
        # volume: orientation B 3 cols × 1 row × 1 layer = 3; weight: 1000/600 = 1 → weight limited
        assert result.weight_limited == 1
        assert result.max_pallets == 1

    def test_pallet_wider_than_vehicle_returns_zero(self):
        too_narrow = VehicleSpec(
            vehicle_type="too_narrow",
            inner_length_mm=5000, inner_width_mm=500,   # narrower than any pallet
            max_height_mm=3000, max_weight_kg=99999,
        )
        result = calculate_loading(too_narrow, eur_pallet())
        assert result.max_pallets == 0

    def test_pallet_taller_than_vehicle_returns_zero(self):
        too_short = VehicleSpec(
            vehicle_type="too_short",
            inner_length_mm=5000, inner_width_mm=3000,
            max_height_mm=500,   # shorter than pallet height (1200mm)
            max_weight_kg=99999,
        )
        result = calculate_loading(too_short, eur_pallet())
        assert result.layers == 0
        assert result.max_pallets == 0
