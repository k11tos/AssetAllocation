#!/usr/bin/python3
"""
Sector Momentum strategy implementation
"""

from typing import Any, Dict, List, Tuple

from config import SECTOR_MOMENTUM_CONFIG

from .base_strategy import BaseStrategy


class SectorMomentumStrategy(BaseStrategy):
    """Sector Momentum 점수 기반 섹터 ETF 전략"""

    def __init__(self):
        super().__init__("SECTOR_MOMENTUM")

    def get_required_data_keys(self) -> List[str]:
        """전략 실행에 필요한 데이터 키 목록"""
        return ["momentum_score", "sma_12month", "today_price"]

    def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        """섹터 모멘텀 전략 배분 계산"""
        momentum_score: Dict[str, float] = data["momentum_score"]
        sma_12month: Dict[str, float] = data["sma_12month"]
        today_price: Dict[str, float] = data["today_price"]

        if not isinstance(momentum_score, dict) or not isinstance(
            sma_12month, dict
        ) or not isinstance(today_price, dict):
            raise ValueError("All inputs must be dictionaries")

        candidates: List[Tuple[str, float]] = []

        if SECTOR_MOMENTUM_CONFIG.SECTOR_TICKERS is None:
            raise ValueError("SECTOR_TICKERS is not configured")

        for ticker in SECTOR_MOMENTUM_CONFIG.SECTOR_TICKERS:
            if ticker not in momentum_score:
                continue

            score = momentum_score[ticker]
            if score <= SECTOR_MOMENTUM_CONFIG.MIN_MOMENTUM_SCORE:
                continue

            if SECTOR_MOMENTUM_CONFIG.REQUIRE_ABOVE_12M_SMA:
                if ticker not in sma_12month or ticker not in today_price:
                    continue
                if today_price[ticker] <= sma_12month[ticker]:
                    continue

            candidates.append((ticker, score))

        candidates.sort(key=lambda x: x[1], reverse=True)

        top_count = SECTOR_MOMENTUM_CONFIG.TOP_COUNT
        slot_size = 100.0 / top_count

        allocation: Dict[str, float] = {}
        selected = candidates[:top_count]

        for ticker, _ in selected:
            allocation[ticker] = allocation.get(ticker, 0.0) + slot_size

        remaining_slots = top_count - len(selected)
        if remaining_slots > 0:
            defensive = SECTOR_MOMENTUM_CONFIG.DEFENSIVE_TICKER
            allocation[defensive] = (
                allocation.get(defensive, 0.0) + remaining_slots * slot_size
            )

        return allocation
