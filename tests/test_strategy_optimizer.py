#!/usr/bin/python3
"""
Unit tests for strategy optimizer helpers
"""

import unittest

from utils.strategy_optimizer import get_required_tickers_for_strategy


class TestStrategyOptimizer(unittest.TestCase):
    """전략별 필요 티커 추출 테스트"""

    def test_get_required_tickers_for_haa_includes_all_universes(self):
        """HAA 티커는 offensive + defensive + canary를 모두 포함해야 함"""
        result = get_required_tickers_for_strategy("haa")
        expected = [
            "SPY",
            "IWM",
            "IEFA",
            "IEMG",
            "VNQ",
            "PDBC",
            "IEF",
            "TLT",
            "BIL",
            "TIP",
        ]

        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
