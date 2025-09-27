#!/usr/bin/python3
"""
MDM (Modified Dual Momentum) strategy implementation
"""

from typing import Any, Dict, List

from config import MDM_CONFIG

from .base_strategy import BaseStrategy


class MDMStrategy(BaseStrategy):
    """MDM (Modified Dual Momentum) 전략"""

    def __init__(self):
        super().__init__("MDM")

    def get_required_data_keys(self) -> List[str]:
        """MDM 전략에 필요한 데이터 키 목록"""
        return ["profit_12month", "profit_6month"]

    def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        MDM 전략 배분을 계산합니다.

        Args:
            data: profit_12month, profit_6month이 포함된 딕셔너리

        Returns:
            자산 배분 딕셔너리
        """
        profit_12month = data["profit_12month"]
        profit_6month = data["profit_6month"]

        mdm: Dict[str, float] = {}

        self.logger.debug(
            f"SPY 12 months average: {round(profit_12month.get('SPY', 0), 3)}"
        )
        self.logger.debug(
            f"IEFA 12 months average: "
            f"{round(profit_12month.get('IEFA', 0), 3)}"
        )

        # 채권들의 6개월 수익률 로깅
        for bond in MDM_CONFIG.BOND_TICKERS:
            if bond in profit_6month:
                self.logger.debug(
                    f"{bond} 6 months average: {round(profit_6month[bond], 3)}"
                )

        # SPY 또는 IEFA의 12개월 수익률이 양수인 경우
        if (
            profit_12month.get("SPY", 0) > 0
            or profit_12month.get("IEFA", 0) > 0
        ):
            if profit_12month.get("SPY", 0) >= profit_12month.get("IEFA", 0):
                mdm["SPY"] = 100
                self.logger.debug("SPY >= IEFA, selecting SPY")
            else:
                mdm["IEFA"] = 100
                self.logger.debug("IEFA > SPY, selecting IEFA")
        else:
            # 채권 동적 자산 배분 실행
            mdm = self._get_bond_dynamic_asset_allocation(profit_6month)

        self.logger.debug(f"MDM allocation: {mdm}")
        return mdm

    def _get_bond_dynamic_asset_allocation(
        self, profit_6month: Dict[str, float]
    ) -> Dict[str, float]:
        """
        채권 동적 자산 배분을 계산합니다.

        Args:
            profit_6month: 6개월 수익률 딕셔너리

        Returns:
            채권 배분 딕셔너리
        """
        bdaa: Dict[str, float] = {}

        # 채권 수익률 딕셔너리 구성
        bond_profit_dict = {
            bond: profit_6month.get(bond, 0)
            for bond in MDM_CONFIG.BOND_TICKERS
        }

        # 상위 3개 채권 선택
        bond_profit_top3 = sorted(
            bond_profit_dict.items(), key=lambda x: x[1], reverse=True
        )[: MDM_CONFIG.TOP_BONDS_COUNT]

        cash: float = 0
        for key, value in bond_profit_top3:
            if value < 0:
                cash += MDM_CONFIG.BOND_ALLOCATION_RATIO
            else:
                bdaa[key] = MDM_CONFIG.BOND_ALLOCATION_RATIO

        if cash > 0:
            bdaa["CASH"] = cash

        self.logger.debug(f"Bond dynamic allocation: {bdaa}")
        return bdaa
