"""
BDAA (Bond Dynamic Asset Allocation) 전략 구현

채권 동적 자산 배분 전략:
- 6개월 수익률 기준으로 상위 N개 채권 선택 (설정 가능)
- 수익률이 음수인 채권은 현금으로 전환
- 각 채권에 균등하게 배분
"""

from typing import Any, Dict, List

from config import BDAA_CONFIG
from strategies.base_strategy import BaseStrategy


class BDAAStrategy(BaseStrategy):
    """BDAA (Bond Dynamic Asset Allocation) 전략 클래스"""

    def __init__(self):
        super().__init__("BDAA")
        self.config = BDAA_CONFIG

    def get_required_data_keys(self) -> List[str]:
        """BDAA 전략에 필요한 데이터 키 목록"""
        return ["profit_6month"]

    def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        BDAA 전략 배분을 계산합니다.

        Args:
            data: profit_6month이 포함된 딕셔너리

        Returns:
            Dict[str, float]: 자산 배분 비율 딕셔너리
        """
        profit_6month = data["profit_6month"]

        self.logger.debug("Starting BDAA allocation calculation")
        self.logger.debug(f"6-month profit data: {profit_6month}")

        # 채권 수익률 딕셔너리 구성
        bond_profit_dict = {
            bond: profit_6month.get(bond, 0)
            for bond in self.config.BOND_TICKERS
        }

        # 상위 N개 채권 선택 (설정값 사용)
        bond_profit_top3 = sorted(
            bond_profit_dict.items(), key=lambda x: x[1], reverse=True
        )[: self.config.TOP_BONDS_COUNT]

        self.logger.debug(
            f"Top {self.config.TOP_BONDS_COUNT} bonds: {bond_profit_top3}"
        )

        bdaa = {}
        cash = 0

        # 각 채권에 대해 배분 결정
        for key, value in bond_profit_top3:
            if value < 0:
                # 수익률이 음수인 경우 현금으로 전환
                cash += self.config.BOND_ALLOCATION_RATIO
                self.logger.debug(
                    f"{key} has negative return ({value:.3f}), "
                    "allocating to cash"
                )
            else:
                # 수익률이 양수인 경우 해당 채권에 배분
                bdaa[key] = self.config.BOND_ALLOCATION_RATIO
                self.logger.debug(
                    f"{key} allocated {self.config.BOND_ALLOCATION_RATIO:.1f}%"
                )

        # 현금 배분
        if cash > 0:
            bdaa["CASH"] = cash
            self.logger.debug(f"Cash allocation: {cash:.1f}%")

        self.logger.debug(f"Final BDAA allocation: {bdaa}")
        return bdaa
