#!/usr/bin/python3
"""
Korean All-Weather strategy implementation
"""

import datetime
from typing import Any, Dict, List

from config import KOREAN_ALL_WEATHER

from .base_strategy import BaseStrategy


class KoreanAllWeatherStrategy(BaseStrategy):
    """한국형 올웨더 전략"""

    def __init__(self):
        super().__init__("Korean All-Weather")

    def get_required_data_keys(self) -> List[str]:
        """한국형 올웨더 전략은 추가 데이터가 필요하지 않습니다."""
        return []

    def _get_execution_month(self) -> int:
        """전략 실행 시점의 현재 달(1~12)을 반환합니다."""
        return datetime.datetime.now().month

    def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        한국형 올웨더 전략 배분을 계산합니다.
        실행 시점의 현재 달 기준으로 비율을 선택합니다.

        Args:
            data: 사용하지 않음 (날짜 기반 전략)

        Returns:
            자산 배분 딕셔너리
        """
        execution_month = self._get_execution_month()

        # 한국형 올웨더 전략 비율 (11~4월 vs 5~10월)
        # 11~4월: 위험자산 중심, 5~10월: 안전자산 중심
        if execution_month in KOREAN_ALL_WEATHER.RISKY_MONTHS:  # 11~4월 전략
            allocation = KOREAN_ALL_WEATHER.RISKY_PERIOD_ALLOCATION.copy()
            self.logger.debug("Using risky period allocation (11~4월)")
        else:  # 5~10월 전략 (안전자산 중심)
            allocation = KOREAN_ALL_WEATHER.SAFE_PERIOD_ALLOCATION.copy()
            self.logger.debug("Using safe period allocation (5~10월)")

        self.logger.debug(
            f"Execution month: {execution_month}, Allocation: {allocation}"
        )
        return allocation
