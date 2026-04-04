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
        tip_momentum = momentum_score_simple.get("TIP", 0)
        bil_momentum = momentum_score_simple.get("BIL", 0)
        ief_momentum = momentum_score_simple.get("IEF", 0)

        # 공격자(OFFENSIVE) 자산 딕셔너리 구성
        attacker_dict = {
            ticker: momentum_score_simple[ticker]
            for ticker in HAA_CONFIG.OFFENSIVE_TICKERS
            if ticker in momentum_score_simple
        }
        self.logger.debug(
            "HAA momentum snapshot: TIP=%.6f, BIL=%.6f, IEF=%.6f",
            tip_momentum,
            bil_momentum,
            ief_momentum,
        )
        self.logger.debug("HAA offensive momentum table: %s", attacker_dict)

        # TIP이 양수인 경우 상위 4개 공격자 자산을 선정하고,
        # 각 슬리브를 개별적으로 절대 모멘텀 필터링한다.
        if tip_momentum > HAA_CONFIG.TIP_THRESHOLD and attacker_dict:
            ranked_offensive_assets = sorted(
                attacker_dict.items(), key=lambda x: x[1], reverse=True
            )
            attacker_profit_top = ranked_offensive_assets[
                : HAA_CONFIG.TOP_ATTACKERS_COUNT
            ]
            self.logger.debug(
                "HAA mode=OFFENSIVE (TIP %.6f > %.6f)",
                tip_momentum,
                HAA_CONFIG.TIP_THRESHOLD,
            )
            self.logger.debug(
                "HAA ranked offensive assets (full): %s", ranked_offensive_assets
            )
            self.logger.debug(
                "HAA selected top %d: %s",
                len(attacker_profit_top),
                attacker_profit_top,
            )

            num_selected = len(attacker_profit_top)
            if num_selected > 0:
                allocation_per_sleeve = (
                    AllocationConstants.FULL_ALLOCATION / num_selected
                )
                defensive_asset = (
                    "BIL" if bil_momentum >= ief_momentum else "IEF"
                )
                self.logger.debug(
                    "HAA replacement defensive asset: %s (BIL=%.6f, IEF=%.6f)",
                    defensive_asset,
                    bil_momentum,
                    ief_momentum,
                )

                for ticker, momentum in attacker_profit_top:
                    if momentum > 0:
                        target_asset = ticker
                    else:
                        target_asset = defensive_asset
                        self.logger.debug(
                            "HAA replacing selected asset %s (momentum=%.6f) -> %s",
                            ticker,
                            momentum,
                            defensive_asset,
                        )
                    haa[target_asset] = (
                        haa.get(target_asset, 0) + allocation_per_sleeve
                    )

        # TIP이 0 이하인 경우 방어 자산(BIL/IEF) 중 모멘텀이 더 높은 자산 선택
        else:
            # 동률이면 현금성 자산인 BIL 우선
            defensive_asset = "BIL" if bil_momentum >= ief_momentum else "IEF"
            haa[defensive_asset] = AllocationConstants.FULL_ALLOCATION
            self.logger.debug(
                "HAA mode=DEFENSIVE (TIP %.6f <= %.6f); selected %s (BIL=%.6f, IEF=%.6f)",
                tip_momentum,
                HAA_CONFIG.TIP_THRESHOLD,
                defensive_asset,
                bil_momentum,
                ief_momentum,
            )

        self.logger.debug("HAA final allocation: %s", haa)
        return haa
