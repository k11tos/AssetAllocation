#!/usr/bin/python3
"""Tests for Sector Momentum strategy."""

import math

from strategies.sector_momentum_strategy import SectorMomentumStrategy


class TestSectorMomentumStrategy:
    def setup_method(self):
        self.strategy = SectorMomentumStrategy()

    def test_top_2_positive_momentum_selected(self):
        momentum_score = {
            "XLK": 1.2,
            "XLC": 0.8,
            "XLI": 0.2,
            "XLF": -0.1,
        }
        sma_12month = {"XLK": 100, "XLC": 90, "XLI": 80, "XLF": 75}
        today_price = {"XLK": 110, "XLC": 95, "XLI": 85, "XLF": 70}

        result = self.strategy.calculate_allocation(
            {
                "momentum_score": momentum_score,
                "sma_12month": sma_12month,
                "today_price": today_price,
            }
        )

        assert result == {"XLK": 50.0, "XLC": 50.0}

    def test_negative_momentum_excluded(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": -0.2, "XLC": 0.4},
                "sma_12month": {"XLK": 100, "XLC": 90},
                "today_price": {"XLK": 105, "XLC": 95},
            }
        )

        assert result == {"XLC": 50.0, "SGOV": 50.0}

    def test_below_12month_sma_excluded(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": 0.6, "XLC": 0.4},
                "sma_12month": {"XLK": 100, "XLC": 90},
                "today_price": {"XLK": 99, "XLC": 95},
            }
        )

        assert result == {"XLC": 50.0, "SGOV": 50.0}

    def test_one_passing_etf_gets_50_and_sgov_50(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": 0.7},
                "sma_12month": {"XLK": 100},
                "today_price": {"XLK": 110},
            }
        )

        assert result == {"XLK": 50.0, "SGOV": 50.0}

    def test_zero_passing_etf_gets_100_sgov(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": -0.1, "XLC": -0.2},
                "sma_12month": {"XLK": 100, "XLC": 90},
                "today_price": {"XLK": 110, "XLC": 95},
            }
        )

        assert result == {"SGOV": 100.0}

    def test_missing_etf_data_skipped_safely(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": 0.9, "XLC": 0.8},
                "sma_12month": {"XLC": 90},
                "today_price": {"XLC": 95},
            }
        )

        assert result == {"XLC": 50.0, "SGOV": 50.0}

    def test_nan_momentum_score_is_skipped(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": math.nan, "XLC": 0.8},
                "sma_12month": {"XLK": 100, "XLC": 90},
                "today_price": {"XLK": 110, "XLC": 95},
            }
        )

        assert result == {"XLC": 50.0, "SGOV": 50.0}

    def test_nan_sma_is_skipped(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": 0.9, "XLC": 0.8},
                "sma_12month": {"XLK": math.nan, "XLC": 90},
                "today_price": {"XLK": 110, "XLC": 95},
            }
        )

        assert result == {"XLC": 50.0, "SGOV": 50.0}

    def test_nan_today_price_is_skipped(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": 0.9, "XLC": 0.8},
                "sma_12month": {"XLK": 100, "XLC": 90},
                "today_price": {"XLK": math.nan, "XLC": 95},
            }
        )

        assert result == {"XLC": 50.0, "SGOV": 50.0}

    def test_inf_and_non_numeric_values_are_skipped(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {
                    "XLK": math.inf,
                    "XLC": 0.8,
                    "XLI": "invalid",
                    "XLF": None,
                    "XLE": -math.inf,
                },
                "sma_12month": {
                    "XLK": 100,
                    "XLC": 90,
                    "XLI": 80,
                    "XLF": 70,
                    "XLE": 60,
                },
                "today_price": {
                    "XLK": 110,
                    "XLC": 95,
                    "XLI": 85,
                    "XLF": 75,
                    "XLE": 65,
                },
            }
        )

        assert result == {"XLC": 50.0, "SGOV": 50.0}

    def test_selected_sector_underperformer_replaced_with_benchmark(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": 1.2, "XLC": 0.8, "SPY": 0.9},
                "sma_12month": {"XLK": 100, "XLC": 90},
                "today_price": {"XLK": 110, "XLC": 95},
            }
        )

        assert result == {"XLK": 50.0, "SPY": 50.0}

    def test_multiple_replacements_accumulate_to_benchmark(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": 0.7, "XLC": 0.6, "SPY": 0.9},
                "sma_12month": {"XLK": 100, "XLC": 90},
                "today_price": {"XLK": 110, "XLC": 95},
            }
        )

        assert result == {"SPY": 100.0}

    def test_benchmark_replacement_keeps_defensive_fill_for_missing_slots(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": 0.7, "SPY": 0.9},
                "sma_12month": {"XLK": 100},
                "today_price": {"XLK": 110},
            }
        )

        assert result == {"SPY": 50.0, "SGOV": 50.0}

    def test_invalid_benchmark_score_keeps_existing_behavior(self):
        result = self.strategy.calculate_allocation(
            {
                "momentum_score": {"XLK": 0.7, "XLC": 0.6, "SPY": math.nan},
                "sma_12month": {"XLK": 100, "XLC": 90},
                "today_price": {"XLK": 110, "XLC": 95},
            }
        )

        assert result == {"XLK": 50.0, "XLC": 50.0}
