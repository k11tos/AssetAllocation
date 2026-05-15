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


def test_get_required_tickers_for_sector_momentum_excludes_defensive_ticker():
    """Sector Momentum 티커는 섹터 ETF만 순서대로 포함해야 함"""
    result = get_required_tickers_for_strategy("sector_momentum")
    expected = [
        "XLK",
        "XLC",
        "XLI",
        "XLF",
        "XLE",
        "XLY",
        "XLP",
        "XLV",
        "XLU",
        "XLB",
        "XLRE",
    ]

    assert result == expected
    assert "SGOV" not in result
    assert len(result) == len(set(result))
