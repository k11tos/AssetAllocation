#!/usr/bin/python3
"""
Unit tests for strategy classes
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from strategies import HAAStrategy, KoreanAllWeatherStrategy


class TestHAAStrategy(unittest.TestCase):
    """HAA 전략 테스트"""

    def setUp(self):
        self.strategy = HAAStrategy()

    def test_get_required_data_keys(self):
        """필요한 데이터 키 목록 테스트"""
        expected_keys = ["momentum_score_simple"]
        self.assertEqual(self.strategy.get_required_data_keys(), expected_keys)

    def test_calculate_allocation_tip_positive(self):
        """TIP이 양수인 경우 테스트"""
        data = {
            "momentum_score_simple": {
                "SPY": 0.1,
                "IWM": 0.2,
                "IEFA": 0.15,
                "IEMG": 0.05,
                "TLT": 0.3,
                "IEF": 0.25,
                "PDBC": 0.1,
                "VNQ": 0.2,
                "TIP": 0.1,  # 양수
            }
        }

        result = self.strategy.calculate_allocation(data)

        # 상위 4개 자산에 25%씩 배분되어야 함
        self.assertEqual(len(result), 4)
        self.assertTrue(all(weight == 25.0 for weight in result.values()))

    def test_calculate_allocation_ief_positive(self):
        """IEF가 양수이고 TIP이 음수인 경우 테스트"""
        data = {
            "momentum_score_simple": {
                "SPY": 0.1,
                "IWM": 0.2,
                "IEFA": 0.15,
                "IEMG": 0.05,
                "TLT": 0.3,
                "IEF": 0.25,
                "PDBC": 0.1,
                "VNQ": 0.2,
                "TIP": -0.1,  # 음수
            }
        }

        result = self.strategy.calculate_allocation(data)

        # IEF에 100% 배분되어야 함
        self.assertEqual(result, {"IEF": 100})

    def test_calculate_allocation_cash(self):
        """TIP과 IEF가 모두 음수인 경우 테스트"""
        data = {
            "momentum_score_simple": {
                "SPY": 0.1,
                "IWM": 0.2,
                "IEFA": 0.15,
                "IEMG": 0.05,
                "TLT": 0.3,
                "IEF": -0.25,
                "PDBC": 0.1,
                "VNQ": 0.2,
                "TIP": -0.1,  # 음수
            }
        }

        result = self.strategy.calculate_allocation(data)

        # 현금에 100% 배분되어야 함
        self.assertEqual(result, {"CASH": 100})

    def test_validate_data(self):
        """데이터 유효성 검증 테스트"""
        # 유효한 데이터 (예외가 발생하지 않아야 함)
        valid_data = {"momentum_score_simple": {"SPY": 0.1}}
        try:
            self.strategy.validate_data(valid_data)
            # 예외가 발생하지 않으면 성공
            self.assertTrue(True)
        except Exception:
            self.fail("Valid data should not raise exception")

        # 유효하지 않은 데이터 (예외가 발생해야 함)
        invalid_data = {"wrong_key": {"SPY": 0.1}}
        with self.assertRaises(Exception):
            self.strategy.validate_data(invalid_data)


class TestKoreanAllWeatherStrategy(unittest.TestCase):
    """한국형 올웨더 전략 테스트"""

    def setUp(self):
        self.strategy = KoreanAllWeatherStrategy()

    def test_get_required_data_keys(self):
        """필요한 데이터 키 목록 테스트"""
        self.assertEqual(self.strategy.get_required_data_keys(), [])

    @patch("strategies.korean_all_weather_strategy.datetime")
    def test_calculate_allocation_risky_period(self, mock_datetime):
        """위험자산 중심 기간 (11~4월) 테스트"""
        # 3월 (위험자산 중심 기간)
        mock_datetime.datetime.now.return_value = datetime(2024, 3, 15)

        result = self.strategy.calculate_allocation({})

        # 위험자산 중심 배분이어야 함
        self.assertIn("TIGER S&P500", result)
        self.assertIn("KOSEF 200TR", result)
        self.assertEqual(result["TIGER S&P500"], 25.0)
        self.assertEqual(result["KOSEF 200TR"], 25.0)

    @patch("strategies.korean_all_weather_strategy.datetime")
    def test_calculate_allocation_safe_period(self, mock_datetime):
        """안전자산 중심 기간 (5~10월) 테스트"""
        # 7월 (안전자산 중심 기간)
        mock_datetime.datetime.now.return_value = datetime(2024, 7, 15)

        result = self.strategy.calculate_allocation({})

        # 안전자산 중심 배분이어야 함
        self.assertIn("TIGER S&P500", result)
        self.assertIn("KOSEF 200TR", result)
        self.assertEqual(result["TIGER S&P500"], 10.0)
        self.assertEqual(result["KOSEF 200TR"], 10.0)

    def test_validate_data(self):
        """데이터 유효성 검증 테스트"""
        # 빈 데이터도 유효해야 함 (추가 데이터가 필요하지 않음)
        try:
            self.strategy.validate_data({})
            # 예외가 발생하지 않으면 성공
            self.assertTrue(True)
        except Exception:
            self.fail(
                "Empty data should not raise exception for Korean All-Weather"
            )


if __name__ == "__main__":
    unittest.main()
