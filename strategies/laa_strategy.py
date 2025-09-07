#!/usr/bin/python3
"""
LAA (Lethargic Asset Allocation) strategy implementation
"""

from typing import Any, Dict

from config import LAA_CONFIG

from .base_strategy import BaseStrategy


class LAAStrategy(BaseStrategy):
    """LAA (Lethargic Asset Allocation) 전략"""

    def __init__(self):
        super().__init__("LAA")

    def get_required_data_keys(self) -> list:
        """LAA 전략에 필요한 데이터 키 목록"""
        return ["sp500", "unrate"]

    def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        LAA 전략 배분을 계산합니다.

        Args:
            data: sp500, unrate 시계열 데이터가 포함된 딕셔너리

        Returns:
            자산 배분 딕셔너리
        """
        sp500 = data["sp500"]
        unrate = data["unrate"]

        laa = LAA_CONFIG.BASE_ALLOCATION.copy()

        # S&P 500 200일 이동평균 계산
        sp500_rolling = sp500.rolling(LAA_CONFIG.SP500_MA_DAYS).mean()
        sp500_average_200days = (
            sp500_rolling.dropna().iloc[-1]
            if not sp500_rolling.dropna().empty
            else sp500.iloc[-1]
        )

        # 실업률 12개월 이동평균 계산
        unrate_rolling = unrate.rolling(LAA_CONFIG.UNRATE_MA_MONTHS).mean()
        unrate_average_12months = (
            unrate_rolling.dropna().iloc[-1]
            if not unrate_rolling.dropna().empty
            else unrate.iloc[-1]
        )

        self.logger.debug(
            f"S&P500 200 days average: {round(sp500_average_200days)}"
        )
        self.logger.debug(f"S&P500 today: {round(sp500.iloc[-1])}")
        self.logger.debug(
            f"Unemployment rate 12 months average: "
            f"{round(unrate_average_12months, 1)}"
        )
        self.logger.debug(
            f"Unemployment rate this month: {round(unrate.iloc[-1], 1)}"
        )

        # 조건에 따른 4번째 자산 선택
        if (
            sp500_average_200days > sp500.iloc[-1]
            and unrate_average_12months < unrate.iloc[-1]
        ):
            laa["SHY"] = LAA_CONFIG.SHY_ALLOCATION
            self.logger.debug("Market conditions favor SHY (bonds)")
        else:
            laa["QQQ"] = LAA_CONFIG.QQQ_ALLOCATION
            self.logger.debug("Market conditions favor QQQ (growth)")

        self.logger.debug(f"LAA allocation: {laa}")
        return laa
