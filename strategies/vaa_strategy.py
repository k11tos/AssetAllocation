#!/usr/bin/python3
"""
VAA (Vigilant Asset Allocation) strategy implementation
"""

from typing import Any, Dict

from config import HAA_CONFIG, VAA_CONFIG

from .base_strategy import BaseStrategy


class VAAStrategy(BaseStrategy):
    """VAA (Vigilant Asset Allocation) 전략"""

    def __init__(self):
        super().__init__("VAA")

    def get_required_data_keys(self) -> list:
        """VAA 전략에 필요한 데이터 키 목록"""
        return ["momentum_score"]

    def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        VAA 전략 배분을 계산합니다.

        Args:
            data: momentum_score가 포함된 딕셔너리

        Returns:
            자산 배분 딕셔너리
        """
        momentum_score = data["momentum_score"]
        vaa = {}

        self.logger.debug("Momentum Scores:")
        for ticker, score in momentum_score.items():
            self.logger.debug(f"{ticker} momentum score: {round(score, 3)}")

        # 모든 모멘텀 스코어가 양수인 경우 공격자 자산 선택
        if all(score >= 0 for score in momentum_score.values()):
            attacker_ticker = max(
                VAA_CONFIG.ATTACKER_TICKERS,
                key=lambda x: momentum_score.get(x, float("-inf")),
            )
            vaa[attacker_ticker] = 100
            self.logger.debug(
                f"All momentum scores >= 0, selecting attacker: "
                f"{attacker_ticker}"
            )
        else:
            # 그렇지 않은 경우 방어자 자산 선택
            defender_ticker = max(
                VAA_CONFIG.DEFENDER_TICKERS,
                key=lambda x: momentum_score.get(x, float("-inf")),
            )
            vaa[defender_ticker] = 100
            self.logger.debug(
                f"Some momentum scores < 0, selecting defender: "
                f"{defender_ticker}"
            )

        self.logger.debug(f"VAA allocation: {vaa}")
        return vaa
