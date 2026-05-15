#!/usr/bin/python3
"""Sector Momentum strategy implementation."""

from typing import Any, Dict, List

from config import SECTOR_MOMENTUM_CONFIG

from .base_strategy import BaseStrategy


class SectorMomentumStrategy(BaseStrategy):
    """Sector Momentum 전략"""

    def __init__(self):
        super().__init__("SECTOR_MOMENTUM")

    def get_required_data_keys(self) -> List[str]:
        """Sector Momentum 전략에 필요한 데이터 키 목록"""
        return ["momentum_score", "sma_12month", "today_price"]

    def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Sector Momentum 전략 배분을 계산합니다."""
        momentum_score = data["momentum_score"]
        sma_12month = data["sma_12month"]
        today_price = data["today_price"]

        sector_tickers = SECTOR_MOMENTUM_CONFIG.SECTOR_TICKERS
        if not sector_tickers:
            raise ValueError("SECTOR_TICKERS is not configured")

        required_inputs = [momentum_score, sma_12month, today_price]
        if all(not source for source in required_inputs):
            raise ValueError("All required inputs are empty")

        candidates: List[str] = []

        for ticker in sector_tickers:
            if ticker not in momentum_score:
                continue

            if SECTOR_MOMENTUM_CONFIG.REQUIRE_ABOVE_12M_SMA:
                if ticker not in sma_12month or ticker not in today_price:
                    continue

            score = momentum_score[ticker]
            if score <= SECTOR_MOMENTUM_CONFIG.MIN_MOMENTUM_SCORE:
                continue

            if SECTOR_MOMENTUM_CONFIG.REQUIRE_ABOVE_12M_SMA:
                if today_price[ticker] <= sma_12month[ticker]:
                    continue

            candidates.append(ticker)

        ranked_candidates = sorted(
            candidates,
            key=lambda ticker: momentum_score[ticker],
            reverse=True,
        )
        selected = ranked_candidates[: SECTOR_MOMENTUM_CONFIG.TOP_COUNT]

        slot_size = 100.0 / SECTOR_MOMENTUM_CONFIG.TOP_COUNT
        allocation: Dict[str, float] = {}

        for ticker in selected:
            allocation[ticker] = allocation.get(ticker, 0.0) + slot_size

        defensive_slots = SECTOR_MOMENTUM_CONFIG.TOP_COUNT - len(selected)
        if defensive_slots > 0:
            defensive_ticker = SECTOR_MOMENTUM_CONFIG.DEFENSIVE_TICKER
            allocation[defensive_ticker] = allocation.get(defensive_ticker, 0.0) + (
                slot_size * defensive_slots
            )

        return allocation
