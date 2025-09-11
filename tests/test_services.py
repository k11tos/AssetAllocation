#!/usr/bin/python3
"""
Unit tests for service classes
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

import requests

from services.communication_service import CommunicationService
from services.data_service import DataService


class TestDataService(unittest.TestCase):
    """DataService 테스트"""

    def setUp(self):
        # 임시 디렉토리에서 테스트
        self.temp_dir = tempfile.mkdtemp()
        self.data_service = DataService(cache_ttl_hours=0.01)  # 매우 짧은 TTL

    def tearDown(self):
        # 임시 파일 정리
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("services.data_service.Fred")
    def test_initialize_fred_success(self, mock_fred_class):
        """FRED 초기화 성공 테스트"""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred

        # 환경변수 모킹
        with patch.dict(os.environ, {"FRED_API_KEY": "test_key"}):
            service = DataService()
            self.assertIsNotNone(service.fred_account)

    @patch("services.data_service.Fred")
    def test_initialize_fred_fallback(self, mock_fred_class):
        """FRED 초기화 fallback 테스트"""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred

        # portfolio.txt 파일 생성
        with open("portfolio.txt", "w") as f:
            f.write("test_key\n")

        try:
            service = DataService()
            self.assertIsNotNone(service.fred_account)
        finally:
            # 테스트 파일 정리
            if os.path.exists("portfolio.txt"):
                os.remove("portfolio.txt")

    @patch("services.data_service.yf.download")
    def test_get_financial_data_success(self, mock_download):
        """금융 데이터 가져오기 성공 테스트"""
        # Mock 데이터 생성 - 충분한 데이터 포인트 제공
        import numpy as np
        import pandas as pd

        # 252개 거래일 데이터 생성 (1년)
        dates = pd.date_range("2023-01-01", periods=252, freq="D")
        spy_data = np.random.randn(252).cumsum() + 100
        qqq_data = np.random.randn(252).cumsum() + 200

        mock_data = pd.DataFrame(
            {("SPY", "Adj Close"): spy_data, ("QQQ", "Adj Close"): qqq_data},
            index=dates,
        )
        mock_download.return_value = mock_data

        result = self.data_service.get_financial_data("SPY QQQ")

        # 결과 검증
        self.assertEqual(len(result), 6)  # 6개 튜플 반환
        (
            momentum_score,
            momentum_score_simple,
            profit_12month,
            profit_6month,
            sma_12month,
            today_price,
        ) = result

        self.assertIn("SPY", momentum_score)
        self.assertIn("QQQ", momentum_score)
        self.assertIn("SPY", today_price)
        self.assertIn("QQQ", today_price)

    @patch("services.data_service.yf.download")
    def test_get_financial_data_no_data(self, mock_download):
        """데이터가 없는 경우 테스트"""
        import pandas as pd

        mock_download.return_value = pd.DataFrame()  # 빈 데이터프레임

        with self.assertRaises(ValueError):
            self.data_service.get_financial_data("INVALID")

    @patch("services.data_service.yf.download")
    def test_get_financial_data_insufficient_data(self, mock_download):
        """데이터가 부족한 경우 테스트 (6개월 데이터 필요)"""
        import pandas as pd

        # 6개월(약 126거래일)보다 적은 데이터 제공
        mock_data = pd.DataFrame(
            {("QQQ", "Adj Close"): [200, 210, 220, 230, 240]}  # 5개 데이터만
        )
        mock_download.return_value = mock_data

        # ta-lib는 데이터가 부족할 때 NaN을 반환하므로 예외 대신 0.0 반환
        result = self.data_service.get_financial_data("QQQ")
        (
            momentum_score,
            momentum_score_simple,
            profit_12month,
            profit_6month,
            sma_12month,
            today_price,
        ) = result

        # 수익률이 0.0으로 반환되는지 확인 (ta-lib가 NaN을 반환하므로 0.0으로 처리됨)
        self.assertEqual(profit_12month["QQQ"], 0.0)
        self.assertEqual(profit_6month["QQQ"], 0.0)

    def test_cache_functionality(self):
        """캐시 기능 테스트"""
        # 캐시 통계 확인
        stats = self.data_service.get_cache_stats()
        self.assertIn("total_files", stats)
        self.assertIn("total_size_bytes", stats)

        # 캐시 정리
        cleared = self.data_service.clear_cache()
        self.assertIsInstance(cleared, int)


class TestCommunicationService(unittest.TestCase):
    """CommunicationService 테스트"""

    def setUp(self):
        self.communication_service = None

    @patch("services.communication_service.telegram.Bot")
    def test_initialize_telegram_success(self, mock_bot_class):
        """텔레그램 초기화 성공 테스트"""
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot

        # 환경변수 모킹
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "test_chat_id",
            },
        ):
            service = CommunicationService()
            self.assertIsNotNone(service.telegram_account)

    @patch("services.communication_service.telegram.Bot")
    def test_send_message_success(self, mock_bot_class):
        """메시지 전송 성공 테스트"""
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot

        # 환경변수 모킹
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "test_chat_id",
            },
        ):
            service = CommunicationService()

            # requests.post 모킹
            with patch(
                "services.communication_service.requests.post"
            ) as mock_post:
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_post.return_value = mock_response

                result = service.send_message("Test message")
                self.assertTrue(result)
                mock_post.assert_called_once()

    @patch("services.communication_service.telegram.Bot")
    def test_send_message_failure(self, mock_bot_class):
        """메시지 전송 실패 테스트"""
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot

        # 환경변수 모킹
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "test_chat_id",
            },
        ):
            service = CommunicationService()

            # requests.post 실패 모킹
            with patch(
                "services.communication_service.requests.post"
            ) as mock_post:
                mock_post.side_effect = Exception("Network error")

                result = service.send_message("Test message")
                self.assertFalse(result)
                mock_post.assert_called_once()

    def test_get_telegram_bot_invalid_mode(self):
        """잘못된 모드로 봇 가져오기 테스트"""
        # 텔레그램이 초기화되지 않은 상태
        service = CommunicationService.__new__(CommunicationService)
        service.telegram_account = None

        result = service.get_telegram_bot("invalid_mode")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
