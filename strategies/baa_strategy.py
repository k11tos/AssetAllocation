#!/usr/bin/python3
"""
BAA (Bold Asset Allocation) strategy implementation
"""

from typing import Any, Dict, List

from config import BAA_CONFIG

from .base_strategy import BaseStrategy


class BAAStrategy(BaseStrategy):
    """BAA (Bold Asset Allocation) 전략"""

    def __init__(self):
        super().__init__("BAA")

    def get_required_data_keys(self) -> List[str]:
        """BAA 전략에 필요한 데이터 키 목록"""
        return ["momentum_score", "sma_12month", "today_price"]

    def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        BAA 전략 배분을 계산합니다.

        Args:
            data: momentum_score, sma_12month, today_price가 포함된 딕셔너리

        Returns:
            자산 배분 딕셔너리
        """
        momentum_score = data["momentum_score"]
        sma_12month = data["sma_12month"]
        today_price = data["today_price"]

        baa = {}

        # 공격자 티커의 모멘텀 스코어가 모두 양수인지 확인 (캐너리 신호)
        if BAA_CONFIG.ATTACKER_TICKERS is None:
            raise ValueError("ATTACKER_TICKERS is not configured")
        attacker_momentum_score = {
            ticker: score
            for ticker, score in momentum_score.items()
            if ticker in BAA_CONFIG.ATTACKER_TICKERS
        }

        canary = all(
            momentum_score.get(ticker, 0) >= 0
            for ticker in BAA_CONFIG.ATTACKER_TICKERS
        )

        if canary and attacker_momentum_score:
            # 공격자 자산 중 최고 모멘텀 스코어 자산 선택
            top_attacker = max(
                attacker_momentum_score,
                key=lambda x: attacker_momentum_score[x],
            )
            baa[top_attacker] = 100.0
            self.logger.debug(
                f"Canary signal positive, selecting attacker: {top_attacker}"
            )
        else:
            if canary and not attacker_momentum_score:
                self.logger.warning(
                    "Canary signal positive but no attacker data found. "
                    "Switching to defensive mode."
                )

            # 방어자 자산들의 가격/이동평균 비율 계산
            price_index = {
                defender: today_price[defender] / sma_12month[defender]
                for defender in BAA_CONFIG.DEFENDER_TICKERS
                if defender in today_price and defender in sma_12month
            }

            # 상위 3개 방어자 자산 선택
            top_defenders = dict(
                sorted(price_index.items(), key=lambda x: x[1], reverse=True)[
                    : BAA_CONFIG.TOP_DEFENDERS_COUNT
                ]
            )

            bil = 0.0
            for defender in top_defenders.keys():
                if (
                    defender == "BIL"
                    or today_price[defender] < sma_12month[defender]
                ):
                    bil += 100.0 / BAA_CONFIG.TOP_DEFENDERS_COUNT
                else:
                    baa[defender] = 100.0 / BAA_CONFIG.TOP_DEFENDERS_COUNT

            if bil != 0:
                baa["BIL"] = bil

            self.logger.debug(
                f"Canary signal negative, using defenders: "
                f"{list(top_defenders.keys())}"
            )

        self.logger.debug(f"BAA allocation: {baa}")
        return baa
