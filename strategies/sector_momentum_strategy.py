#!/usr/bin/python3
"""
Sector Momentum strategy implementation
"""

import math
from typing import Any, Dict, List, Tuple

from config import SECTOR_MOMENTUM_CONFIG

from .base_strategy import BaseStrategy


def _is_finite_number(value: Any) -> bool:
    """값이 유한한 숫자인지 확인합니다."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return False

    return math.isfinite(numeric_value)


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

            raw_score = momentum_score[ticker]
            if not _is_finite_number(raw_score):
                continue
            score = float(raw_score)

            if score <= SECTOR_MOMENTUM_CONFIG.MIN_MOMENTUM_SCORE:
                continue

            if SECTOR_MOMENTUM_CONFIG.REQUIRE_ABOVE_12M_SMA:
                if ticker not in sma_12month or ticker not in today_price:
                    continue

                raw_sma = sma_12month[ticker]
                raw_today = today_price[ticker]
                if not _is_finite_number(raw_sma) or not _is_finite_number(
                    raw_today
                ):
                    continue

                sma_value = float(raw_sma)
                today_value = float(raw_today)
                if today_value <= sma_value:
                    continue

            candidates.append((ticker, score))

        candidates.sort(key=lambda x: x[1], reverse=True)

        top_count = SECTOR_MOMENTUM_CONFIG.TOP_COUNT
        slot_size = 100.0 / top_count

        allocation: Dict[str, float] = {}
        selected = candidates[:top_count]
        selected = self._replace_underperformers_with_benchmark(
            selected=selected,
            momentum_score=momentum_score,
            slot_size=slot_size,
        )

        for ticker, _ in selected:
            allocation[ticker] = allocation.get(ticker, 0.0) + slot_size

        remaining_slots = top_count - len(selected)
        if remaining_slots > 0:
            defensive = SECTOR_MOMENTUM_CONFIG.DEFENSIVE_TICKER
            allocation[defensive] = (
                allocation.get(defensive, 0.0) + remaining_slots * slot_size
            )

        return allocation

    def _replace_underperformers_with_benchmark(
        self,
        selected: List[Tuple[str, float]],
        momentum_score: Dict[str, float],
        slot_size: float,
    ) -> List[Tuple[str, float]]:
        """선정된 섹터 ETF 중 벤치마크보다 약한 종목을 벤치마크로 대체"""
        if not SECTOR_MOMENTUM_CONFIG.REPLACE_WITH_BENCHMARK_IF_UNDERPERFORMING:
            return selected

        benchmark_ticker = SECTOR_MOMENTUM_CONFIG.BENCHMARK_TICKER
        benchmark_raw_score = momentum_score.get(benchmark_ticker)
        if not _is_finite_number(benchmark_raw_score):
            self.logger.debug(
                "Sector Momentum benchmark replacement skipped: %s momentum score is missing or invalid (%r)",
                benchmark_ticker,
                benchmark_raw_score,
            )
            return selected

        benchmark_score = float(benchmark_raw_score)

        replaced: List[Tuple[str, float]] = []
        for ticker, sector_score in selected:
            if sector_score < benchmark_score:
                self.logger.info(
                    "Sector Momentum benchmark replacement: %s score=%.4f < %s score=%.4f, allocating %.2f%% to %s",
                    ticker,
                    sector_score,
                    benchmark_ticker,
                    benchmark_score,
                    slot_size,
                    benchmark_ticker,
                )
                replaced.append((benchmark_ticker, benchmark_score))
            else:
                replaced.append((ticker, sector_score))

        return replaced
