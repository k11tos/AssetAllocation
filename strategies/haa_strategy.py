#!/usr/bin/python3
"""
HAA (Hybrid Asset Allocation) strategy implementation
"""

from typing import Any, Dict, List

from config import HAA_CONFIG

from .base_strategy import BaseStrategy


class AllocationConstants:
    """자산 배분 관련 상수들"""

    # 기본 배분 비율
    FULL_ALLOCATION = 100.0


class HAAStrategy(BaseStrategy):
    """HAA (Hybrid Asset Allocation) 전략"""

    def __init__(self):
        super().__init__("HAA")

    def get_required_data_keys(self) -> List[str]:
        """HAA 전략에 필요한 데이터 키 목록"""
        return ["momentum_score_simple"]

    def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        HAA 전략 배분을 계산합니다.

        Args:
            data: momentum_score_simple이 포함된 딕셔너리

        Returns:
            자산 배분 딕셔너리
        """
        momentum_score_simple = data["momentum_score_simple"]
        haa = {}

        # 공격자(OFFENSIVE) 자산 딕셔너리 구성
        attacker_dict = {
            ticker: momentum_score_simple[ticker]
            for ticker in HAA_CONFIG.OFFENSIVE_TICKERS
            if ticker in momentum_score_simple
        }

        # TIP이 양수인 경우 상위 4개 공격자 자산에 균등 배분
        if (
            momentum_score_simple.get("TIP", 0) > HAA_CONFIG.TIP_THRESHOLD
            and attacker_dict
        ):
            attacker_profit_top4 = dict(
                sorted(
                    attacker_dict.items(), key=lambda x: x[1], reverse=True
                )[: HAA_CONFIG.TOP_ATTACKERS_COUNT]
            )
            # 실제 선택된 자산 수로 나누어 항상 100% 배분 보장
            num_selected = len(attacker_profit_top4)
            if num_selected > 0:
                allocation_per_asset = (
                    AllocationConstants.FULL_ALLOCATION / num_selected
                )
                for key in attacker_profit_top4.keys():
                    haa[key] = allocation_per_asset
            self.logger.debug(
                f"TIP > 0, using top {num_selected} "
                f"attackers: {list(attacker_profit_top4.keys())}"
            )

        # IEF가 양수인 경우 IEF에 100% 배분
        elif momentum_score_simple.get("IEF", 0) > HAA_CONFIG.IEF_THRESHOLD:
            haa["IEF"] = AllocationConstants.FULL_ALLOCATION
            self.logger.debug("IEF > 0, allocating 100% to IEF")

        # 그 외의 경우 단기국채(BIL) 보유
        else:
            haa["BIL"] = AllocationConstants.FULL_ALLOCATION
            self.logger.debug("TIP and IEF <= 0, allocating 100% to BIL")

        self.logger.debug(f"HAA allocation: {haa}")
        return haa
