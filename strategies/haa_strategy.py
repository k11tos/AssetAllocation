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

        # TIP이 양수인 경우 상위 4개 공격자 자산을 선정하고,
        # 각 슬리브를 개별적으로 절대 모멘텀 필터링한다.
        if (
            momentum_score_simple.get("TIP", 0) > HAA_CONFIG.TIP_THRESHOLD
            and attacker_dict
        ):
            attacker_profit_top = sorted(
                attacker_dict.items(), key=lambda x: x[1], reverse=True
            )[: HAA_CONFIG.TOP_ATTACKERS_COUNT]

            num_selected = len(attacker_profit_top)
            if num_selected > 0:
                allocation_per_sleeve = (
                    AllocationConstants.FULL_ALLOCATION / num_selected
                )
                bil_momentum = momentum_score_simple.get("BIL", 0)
                ief_momentum = momentum_score_simple.get("IEF", 0)
                defensive_asset = (
                    "BIL" if bil_momentum >= ief_momentum else "IEF"
                )

                for ticker, momentum in attacker_profit_top:
                    target_asset = (
                        ticker if momentum > 0 else defensive_asset
                    )
                    haa[target_asset] = (
                        haa.get(target_asset, 0) + allocation_per_sleeve
                    )

            self.logger.debug(
                f"TIP > 0, top attackers: {[t for t, _ in attacker_profit_top]}, "
                f"allocation: {haa}"
            )

        # TIP이 0 이하인 경우 방어 자산(BIL/IEF) 중 모멘텀이 더 높은 자산 선택
        else:
            bil_momentum = momentum_score_simple.get("BIL", 0)
            ief_momentum = momentum_score_simple.get("IEF", 0)

            # 동률이면 현금성 자산인 BIL 우선
            defensive_asset = "BIL" if bil_momentum >= ief_momentum else "IEF"
            haa[defensive_asset] = AllocationConstants.FULL_ALLOCATION
            self.logger.debug(
                f"TIP <= 0, selecting defensive asset: {defensive_asset} "
                f"(BIL={bil_momentum}, IEF={ief_momentum})"
            )

        self.logger.debug(f"HAA allocation: {haa}")
        return haa
