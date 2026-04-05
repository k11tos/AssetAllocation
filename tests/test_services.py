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
        self.api_config_patcher = patch(
            "services.data_service.API_CONFIG.FRED_API_KEY",
            "1234567890abcdef1234567890abcdef",
        )
        self.api_config_patcher.start()
        self.data_service = DataService(cache_ttl_hours=0.01)  # 매우 짧은 TTL

    def tearDown(self):
        # 임시 파일 정리
        import shutil

        self.api_config_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("services.data_service.Fred")
    def test_initialize_fred_success(self, mock_fred_class):
        """FRED 초기화 성공 테스트"""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred

        with patch(
            "services.data_service.API_CONFIG.FRED_API_KEY",
            "abcdef1234567890abcdef1234567890",
        ):
            service = DataService()
            self.assertIsNotNone(service.fred_account)

    @patch("services.data_service.Fred")
    def test_initialize_fred_fallback(self, mock_fred_class):
        """FRED 초기화 fallback 테스트"""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred

        # 테스트 전용 fallback 파일을 사용해 작업 디렉토리 의존성 제거
        fd, fallback_path = tempfile.mkstemp(
            prefix="portfolio_test_",
            suffix=".txt",
            dir=os.getcwd(),
        )
        with os.fdopen(fd, "w", encoding="utf-8") as file_descriptor:
            file_descriptor.write("abcdef1234567890abcdef1234567890\n")

        try:
            with patch(
                "services.data_service.API_CONFIG.FRED_API_KEY",
                "",
            ), patch(
                "services.data_service.API_CONFIG.FALLBACK_FILE",
                fallback_path,
            ):
                service = DataService()
                self.assertIsNotNone(service.fred_account)
        finally:
            os.remove(fallback_path)

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

        from exceptions import DataRetrievalError

        mock_download.return_value = pd.DataFrame()  # 빈 데이터프레임

        with self.assertRaises(DataRetrievalError):
            self.data_service.get_financial_data("INVALID")

    @patch("services.data_service.yf.download")
    def test_get_financial_data_records_completed_month_end_as_evaluation_date(
        self, mock_download
    ):
        """HAA 보고용 기준일은 최신 일봉이 아닌 최신 완료 월말 거래일이어야 함"""
        import pandas as pd

        mock_data = pd.DataFrame(
            {("SPY", "Adj Close"): [100.0, 110.0, 120.0]},
            index=pd.to_datetime(["2026-02-27", "2026-03-31", "2026-04-03"]),
        )
        mock_download.return_value = mock_data

        with patch("services.data_service.pd.Timestamp.now") as mock_now:
            mock_now.return_value = pd.Timestamp("2026-04-04")
            self.data_service.get_financial_data("SPY")

        self.assertEqual(self.data_service.get_last_market_data_date(), "2026-03-31")

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

    @patch("services.data_service.ta.SMA")
    @patch("services.data_service.yf.download")
    def test_get_financial_data_simple_momentum_is_average(
        self, mock_download, mock_sma
    ):
        """단순 모멘텀은 월말 1/3/6/12개월 수익률의 평균이어야 함"""
        import numpy as np
        import pandas as pd

        dates = pd.date_range("2023-01-01", periods=260, freq="D")
        prices = np.linspace(100, 120, 260)
        mock_data = pd.DataFrame(
            {("SPY", "Adj Close"): prices},
            index=dates,
        )
        mock_download.return_value = mock_data
        mock_sma.return_value = np.array([110.0])

        with patch.object(
            self.data_service.cache_manager, "get", return_value=None
        ), patch.object(
            self.data_service,
            "_calculate_month_end_returns",
            return_value={1: 0.04, 3: 0.06, 6: 0.08, 12: 0.12},
        ):
            (
                _momentum_score,
                momentum_score_simple,
                _profit_12month,
                _profit_6month,
                _sma_12month,
                _today_price,
            ) = self.data_service.get_financial_data("SPY")

        # (0.04 + 0.06 + 0.08 + 0.12) / 4 = 0.075
        self.assertAlmostEqual(momentum_score_simple["SPY"], 0.075, places=9)

    def test_extract_month_end_prices_keeps_holiday_shortened_month_end(self):
        """거래소 휴장으로 마지막 거래일이 앞당겨진 월도 월말 데이터로 유지해야 함"""
        import pandas as pd

        prices = pd.Series(
            [100.0, 110.0],
            index=pd.to_datetime(
                [
                    "2021-11-30",  # 정상 월말
                    "2021-12-30",  # 12/31 휴장(신정 대체휴일)으로 실질 월말
                ]
            ),
        )

        month_end_prices = self.data_service._extract_month_end_prices(prices)

        self.assertEqual(len(month_end_prices), 2)
        self.assertAlmostEqual(month_end_prices.iloc[-1], 110.0)

    def test_extract_month_end_prices_excludes_in_progress_current_month(self):
        """진행 중인 현재 월 데이터는 HAA 월말 앵커에서 제외되어야 함"""
        import pandas as pd

        prices = pd.Series(
            [100.0, 110.0, 120.0],
            index=pd.to_datetime(["2026-02-28", "2026-03-31", "2026-04-03"]),
        )

        month_end_prices = self.data_service._extract_month_end_prices(
            prices,
            drop_incomplete_current_month=True,
            as_of_date=pd.Timestamp("2026-04-04"),
        )

        self.assertEqual(len(month_end_prices), 2)
        self.assertEqual(month_end_prices.index[-1], pd.Timestamp("2026-03-31"))
        self.assertAlmostEqual(month_end_prices.iloc[-1], 110.0)

    def test_extract_month_end_prices_excludes_month_even_on_month_end(self):
        """월말 당일이어도 현재 달은 HAA 월말 앵커에서 제외되어야 함"""
        import pandas as pd

        prices = pd.Series(
            [100.0, 110.0],
            index=pd.to_datetime(["2026-02-27", "2026-03-31"]),
        )

        month_end_prices = self.data_service._extract_month_end_prices(
            prices,
            drop_incomplete_current_month=True,
            as_of_date=pd.Timestamp("2026-03-31"),
        )

        self.assertEqual(len(month_end_prices), 1)
        self.assertEqual(month_end_prices.index[-1], pd.Timestamp("2026-02-27"))

    def test_extract_month_end_prices_keeps_prior_month_after_next_month_begins(self):
        """다음 달이 시작되면 직전 달 마지막 거래일은 유효 월말로 유지되어야 함"""
        import pandas as pd

        prices = pd.Series(
            [100.0, 110.0],
            index=pd.to_datetime(["2026-02-27", "2026-03-31"]),
        )

        month_end_prices = self.data_service._extract_month_end_prices(
            prices,
            drop_incomplete_current_month=True,
            as_of_date=pd.Timestamp("2026-04-01"),
        )

        self.assertEqual(len(month_end_prices), 2)
        self.assertEqual(month_end_prices.index[-1], pd.Timestamp("2026-03-31"))

    def test_calculate_month_end_returns_keeps_holiday_shortened_latest_month(self):
        """휴장으로 마지막 거래일이 월말 이전이어도 최신 월을 드롭하지 않아야 함"""
        import pandas as pd

        prices = pd.Series(
            [100.0, 110.0, 120.0, 130.0],
            index=pd.to_datetime(
                [
                    "2021-09-30",
                    "2021-10-29",
                    "2021-11-30",
                    "2021-12-30",  # 12/31 휴장
                ]
            ),
        )

        month_end_returns = self.data_service._calculate_month_end_returns(prices)

        # 최신 월(12월)을 유지해야 1개월 수익률이 130/120-1로 계산됨
        self.assertAlmostEqual(month_end_returns[1], (130.0 / 120.0) - 1.0)
        self.assertAlmostEqual(month_end_returns[3], (130.0 / 100.0) - 1.0)
        self.assertEqual(month_end_returns[6], 0.0)
        self.assertEqual(month_end_returns[12], 0.0)

    def test_calculate_month_end_returns_handles_insufficient_completed_history(self):
        """완료된 월 이력이 부족하면 안전하게 0.0 수익률을 반환해야 함"""
        import pandas as pd

        prices = pd.Series(
            [100.0, 105.0],
            index=pd.to_datetime(["2026-03-31", "2026-04-03"]),
        )

        with patch("services.data_service.pd.Timestamp.now") as mock_now:
            mock_now.return_value = pd.Timestamp("2026-04-04")
            returns = self.data_service._calculate_month_end_returns(prices)

        self.assertEqual(returns[1], 0.0)
        self.assertEqual(returns[3], 0.0)
        self.assertEqual(returns[6], 0.0)
        self.assertEqual(returns[12], 0.0)

    def test_calculate_month_end_returns_for_13612_lookbacks(self):
        """월말 샘플 기준 1/3/6/12개월 수익률을 정확히 계산해야 함"""
        import pandas as pd

        month_end_dates = pd.date_range("2025-01-31", periods=13, freq="BME")
        month_end_prices = [100.0 + i * 10.0 for i in range(13)]
        prices = pd.Series(month_end_prices, index=month_end_dates)

        month_end_returns = self.data_service._calculate_month_end_returns(prices)

        self.assertAlmostEqual(month_end_returns[1], (220.0 / 210.0) - 1.0)
        self.assertAlmostEqual(month_end_returns[3], (220.0 / 190.0) - 1.0)
        self.assertAlmostEqual(month_end_returns[6], (220.0 / 160.0) - 1.0)
        self.assertAlmostEqual(month_end_returns[12], (220.0 / 100.0) - 1.0)

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
        self.bot_token_patcher = patch(
            "services.communication_service.API_CONFIG.TELEGRAM_BOT_TOKEN",
            "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
        )
        self.chat_id_patcher = patch(
            "services.communication_service.API_CONFIG.TELEGRAM_CHAT_ID",
            "123456789",
        )
        self.bot_token_patcher.start()
        self.chat_id_patcher.start()

    def tearDown(self):
        self.bot_token_patcher.stop()
        self.chat_id_patcher.stop()

    @patch("services.communication_service.telegram.Bot")
    def test_initialize_telegram_success(self, mock_bot_class):
        """텔레그램 초기화 성공 테스트"""
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot

        service = CommunicationService()
        self.assertIsNotNone(service.telegram_account)

    @patch("services.communication_service.telegram.Bot")
    def test_send_message_success(self, mock_bot_class):
        """메시지 전송 성공 테스트"""
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot

        service = CommunicationService()

        # self.session.post 모킹
        with patch.object(service.session, "post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "result": {
                    "message_id": 101,
                    "chat": {"id": 123456789, "type": "private"},
                }
            }
            mock_post.return_value = mock_response

            result = service.send_message("Test message")
            self.assertTrue(result)
            mock_post.assert_called_once()

    @patch("services.communication_service.telegram.Bot")
    def test_send_message_failure(self, mock_bot_class):
        """메시지 전송 실패 테스트"""
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot

        service = CommunicationService()

        # self.session.post 실패 모킹
        with patch.object(service.session, "post") as mock_post:
            mock_post.side_effect = Exception("Network error")

            result = service.send_message("Test message")
            self.assertFalse(result)
            mock_post.assert_called_once()

    @patch("services.communication_service.telegram.Bot")
    def test_send_messages_success(self, mock_bot_class):
        """메시지 목록 전송 성공 테스트"""
        mock_bot_class.return_value = Mock()
        service = CommunicationService()

        with patch.object(service, "send_message", return_value=True) as mock_send:
            result = service.send_messages(["line1", "line2"])

        self.assertTrue(result)
        self.assertEqual(mock_send.call_count, 2)
        self.assertEqual(
            [call.args[0] for call in mock_send.call_args_list],
            ["line1", "line2"],
        )

    @patch("services.communication_service.telegram.Bot")
    def test_send_message_single_string_input_makes_one_send_call(
        self, mock_bot_class
    ):
        """문자열 단일 입력은 Telegram API 호출을 한 번만 수행해야 함"""
        mock_bot_class.return_value = Mock()
        service = CommunicationService()

        with patch.object(service.session, "post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "result": {
                    "message_id": 201,
                    "chat": {"id": 123456789, "type": "private"},
                }
            }
            mock_post.return_value = mock_response

            result = service.send_message("single payload")

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("services.communication_service.telegram.Bot")
    def test_send_messages_fail_fast_on_first_failure(self, mock_bot_class):
        """첫 번째 실패 시 후속 메시지 전송을 중단해야 함"""
        mock_bot_class.return_value = Mock()
        service = CommunicationService()

        with patch.object(
            service, "send_message", side_effect=[False, True]
        ) as mock_send:
            result = service.send_messages(["line1", "line2"])

        self.assertFalse(result)
        self.assertEqual(mock_send.call_count, 1)

    @patch("services.communication_service.telegram.Bot")
    def test_send_messages_rejects_string_payload(self, mock_bot_class):
        """문자열 단일 payload는 목록으로 간주하지 않아야 함"""
        mock_bot_class.return_value = Mock()
        service = CommunicationService()

        result = service.send_messages("not-a-list")
        self.assertFalse(result)

    @patch("services.communication_service.telegram.Bot")
    def test_send_messages_logs_and_reraises_late_exception(
        self, mock_bot_class
    ):
        """후속 메시지 예외는 로그에 남기고 다시 발생시켜야 함"""
        mock_bot_class.return_value = Mock()
        service = CommunicationService()

        with patch.object(
            service,
            "send_message",
            side_effect=[True, RuntimeError("boom on second message")],
        ):
            with self.assertLogs(
                "services.communication_service", level="ERROR"
            ) as captured_logs:
                with self.assertRaises(RuntimeError):
                    service.send_messages(["line1", "line2"])

        self.assertTrue(
            any(
                "Telegram multi-send raised at message_index=2/2" in log
                for log in captured_logs.output
            )
        )
        self.assertTrue(
            any("boom on second message" in log for log in captured_logs.output)
        )

    def test_get_telegram_bot_invalid_mode(self):
        """잘못된 모드로 봇 가져오기 테스트"""
        # 텔레그램이 초기화되지 않은 상태
        service = CommunicationService.__new__(CommunicationService)
        service.telegram_account = None

        result = service.get_telegram_bot("invalid_mode")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
