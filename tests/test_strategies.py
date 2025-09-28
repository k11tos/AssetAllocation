#!/usr/bin/python3
"""
Unit tests for strategy classes
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from strategies import (
    BAAStrategy,
    HAAStrategy,
    KoreanAllWeatherStrategy,
    VAAStrategy,
)


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


class TestBAAStrategy(unittest.TestCase):
    """BAA 전략 테스트"""

    def setUp(self):
        self.strategy = BAAStrategy()

    def test_get_required_data_keys(self):
        """필요한 데이터 키 목록 테스트"""
        expected_keys = ["momentum_score", "sma_12month", "today_price"]
        self.assertEqual(self.strategy.get_required_data_keys(), expected_keys)

    def test_calculate_allocation_canary_positive(self):
        """캐너리 신호가 양수인 경우 테스트 (공격자 자산 선택)"""
        data = {
            "momentum_score": {
                "QQQ": 0.1,  # 공격자 자산
                "IEFA": 0.2,  # 공격자 자산 - 최고
                "IEMG": 0.15,  # 공격자 자산
                "AGG": 0.05,  # 공격자 자산
                "TLT": 0.3,  # 방어자 자산 (공격자에 없음)
                "IEF": 0.25,  # 방어자 자산 (공격자에 없음)
                "PDBC": 0.1,  # 방어자 자산 (공격자에 없음)
                "VNQ": 0.2,  # 방어자 자산 (공격자에 없음)
            },
            "sma_12month": {
                "QQQ": 100.0,
                "IEFA": 200.0,
                "IEMG": 150.0,
                "AGG": 50.0,
                "TLT": 300.0,
                "IEF": 250.0,
                "PDBC": 100.0,
                "VNQ": 200.0,
            },
            "today_price": {
                "QQQ": 110.0,
                "IEFA": 220.0,
                "IEMG": 165.0,
                "AGG": 55.0,
                "TLT": 330.0,
                "IEF": 275.0,
                "PDBC": 110.0,
                "VNQ": 220.0,
            },
        }

        result = self.strategy.calculate_allocation(data)

        # 공격자 자산 중 최고 모멘텀 스코어 자산에 100% 배분
        self.assertEqual(len(result), 1)
        self.assertEqual(list(result.values())[0], 100.0)
        # IEFA가 공격자 자산 중 최고 모멘텀 스코어 (0.2)
        self.assertIn("IEFA", result)

    def test_calculate_allocation_canary_negative(self):
        """캐너리 신호가 음수인 경우 테스트 (방어자 자산 선택)"""
        data = {
            "momentum_score": {
                "QQQ": -0.1,  # 공격자 자산 - 음수
                "IEFA": -0.2,  # 공격자 자산 - 음수
                "IEMG": -0.15,  # 공격자 자산 - 음수
                "AGG": -0.05,  # 공격자 자산 - 음수
                "BIL": 0.1,  # 방어자 자산
                "IEF": 0.25,  # 방어자 자산
                "TLT": 0.3,  # 방어자 자산 - 최고
                "LQD": 0.2,  # 방어자 자산
                "TIP": 0.15,  # 방어자 자산
                "BND": 0.1,  # 방어자 자산
                "DBC": 0.05,  # 방어자 자산
            },
            "sma_12month": {
                "QQQ": 100.0,
                "IEFA": 200.0,
                "IEMG": 150.0,
                "AGG": 50.0,
                "BIL": 50.0,
                "IEF": 250.0,
                "TLT": 300.0,
                "LQD": 200.0,
                "TIP": 150.0,
                "BND": 100.0,
                "DBC": 50.0,
            },
            "today_price": {
                "QQQ": 110.0,
                "IEFA": 220.0,
                "IEMG": 165.0,
                "AGG": 55.0,
                "BIL": 55.0,  # SMA보다 높음
                "IEF": 275.0,  # SMA보다 높음
                "TLT": 330.0,  # SMA보다 높음
                "LQD": 220.0,  # SMA보다 높음
                "TIP": 165.0,  # SMA보다 높음
                "BND": 110.0,  # SMA보다 높음
                "DBC": 55.0,  # SMA보다 높음
            },
        }

        result = self.strategy.calculate_allocation(data)

        # 방어자 자산들에 배분되어야 함 (상위 3개)
        self.assertEqual(len(result), 3)  # TOP_DEFENDERS_COUNT = 3
        # 총 배분이 100%여야 함
        total_allocation = sum(result.values())
        self.assertAlmostEqual(total_allocation, 100.0, places=1)

    def test_calculate_allocation_with_bil(self):
        """BIL이 포함된 방어자 자산 테스트"""
        data = {
            "momentum_score": {
                "QQQ": -0.1,  # 공격자 자산 - 음수
                "IEFA": -0.2,  # 공격자 자산 - 음수
                "IEMG": -0.15,  # 공격자 자산 - 음수
                "AGG": -0.05,  # 공격자 자산 - 음수
                "BIL": 0.5,  # 방어자 자산 - 상위 3개에 포함되도록 높게
                "IEF": 0.01,  # 방어자 자산 - 매우 낮게
                "TLT": 0.01,  # 방어자 자산 - 매우 낮게
                "LQD": 0.01,  # 방어자 자산 - 매우 낮게
                "TIP": 0.01,  # 방어자 자산 - 매우 낮게
                "BND": 0.01,  # 방어자 자산 - 매우 낮게
                "DBC": 0.01,  # 방어자 자산 - 매우 낮게
            },
            "sma_12month": {
                "QQQ": 100.0,
                "IEFA": 200.0,
                "IEMG": 150.0,
                "AGG": 50.0,
                "BIL": 50.0,  # price_index = 60/50 = 1.2
                "IEF": 250.0,  # price_index = 250/250 = 1.0
                "TLT": 300.0,  # price_index = 300/300 = 1.0
                "LQD": 200.0,  # price_index = 200/200 = 1.0
                "TIP": 150.0,  # price_index = 150/150 = 1.0
                "BND": 100.0,  # price_index = 100/100 = 1.0
                "DBC": 50.0,  # price_index = 50/50 = 1.0
            },
            "today_price": {
                "QQQ": 110.0,
                "IEFA": 220.0,
                "IEMG": 165.0,
                "AGG": 55.0,
                "BIL": 60.0,  # SMA보다 높음 (price_index 상위 3개에 포함되도록)
                "IEF": 200.0,  # SMA보다 낮음 (BIL 조건)
                "TLT": 250.0,  # SMA보다 낮음 (BIL 조건)
                "LQD": 150.0,  # SMA보다 낮음 (BIL 조건)
                "TIP": 100.0,  # SMA보다 낮음 (BIL 조건)
                "BND": 80.0,  # SMA보다 낮음 (BIL 조건)
                "DBC": 40.0,  # SMA보다 낮음 (BIL 조건)
            },
        }

        result = self.strategy.calculate_allocation(data)

        # BIL이 포함되어야 함 (BIL이 상위 3개에 포함되고 BIL 조건에 의해)
        self.assertIn("BIL", result)
        # 총 배분이 100%여야 함
        total_allocation = sum(result.values())
        self.assertAlmostEqual(total_allocation, 100.0, places=1)
        # BIL에 100% 배분되어야 함 (다른 자산들이 BIL 조건에 해당)
        self.assertEqual(result["BIL"], 100.0)

    def test_validate_data(self):
        """데이터 검증 테스트"""
        # 유효한 데이터
        valid_data = {
            "momentum_score": {"SPY": 0.1, "IWM": 0.2},
            "sma_12month": {"SPY": 100.0, "IWM": 200.0},
            "today_price": {"SPY": 110.0, "IWM": 220.0},
        }

        # 예외가 발생하지 않아야 함
        try:
            self.strategy.validate_data(valid_data)
        except Exception as e:
            self.fail(f"Valid data should not raise exception: {e}")

        # 필수 키가 없는 경우
        invalid_data = {"momentum_score": {"SPY": 0.1}}

        with self.assertRaises(Exception):
            self.strategy.validate_data(invalid_data)


class TestVAAStrategy(unittest.TestCase):
    """VAA 전략 테스트"""

    def setUp(self):
        self.strategy = VAAStrategy()

    def test_get_required_data_keys(self):
        """필요한 데이터 키 목록 테스트"""
        expected_keys = ["momentum_score"]
        self.assertEqual(self.strategy.get_required_data_keys(), expected_keys)

    def test_calculate_allocation_all_positive(self):
        """모든 모멘텀 스코어가 양수인 경우 테스트 (공격자 자산 선택)"""
        data = {
            "momentum_score": {
                "SPY": 0.1,  # 공격자 자산
                "IWM": 0.2,  # 공격자 자산에 없음
                "IEFA": 0.3,  # 공격자 자산 - 최고
                "IEMG": 0.05,  # 공격자 자산
                "TLT": 0.25,  # 공격자 자산에 없음
                "IEF": 0.15,  # 공격자 자산에 없음
                "PDBC": 0.1,  # 공격자 자산에 없음
                "VNQ": 0.2,  # 공격자 자산에 없음
                "AGG": 0.05,  # 공격자 자산
            }
        }

        result = self.strategy.calculate_allocation(data)

        # 공격자 자산 중 최고 모멘텀 스코어 자산에 100% 배분
        self.assertEqual(len(result), 1)
        self.assertEqual(list(result.values())[0], 100.0)
        # IEFA가 공격자 자산 중 최고 모멘텀 스코어 (0.3)
        self.assertIn("IEFA", result)

    def test_calculate_allocation_some_negative(self):
        """일부 모멘텀 스코어가 음수인 경우 테스트 (방어자 자산 선택)"""
        data = {
            "momentum_score": {
                "SPY": -0.1,  # 음수
                "IWM": 0.2,
                "IEFA": 0.15,
                "IEMG": 0.05,
                "TLT": 0.3,
                "IEF": 0.25,
                "PDBC": 0.1,
                "VNQ": 0.2,
            }
        }

        result = self.strategy.calculate_allocation(data)

        # 방어자 자산 중 최고 모멘텀 스코어 자산에 100% 배분
        self.assertEqual(len(result), 1)
        self.assertEqual(list(result.values())[0], 100.0)

    def test_validate_data(self):
        """데이터 검증 테스트"""
        # 유효한 데이터
        valid_data = {"momentum_score": {"SPY": 0.1, "IWM": 0.2}}

        # 예외가 발생하지 않아야 함
        try:
            self.strategy.validate_data(valid_data)
        except Exception as e:
            self.fail(f"Valid data should not raise exception: {e}")

        # 필수 키가 없는 경우
        invalid_data = {"other_key": "value"}

        with self.assertRaises(Exception):
            self.strategy.validate_data(invalid_data)


if __name__ == "__main__":
    unittest.main()
