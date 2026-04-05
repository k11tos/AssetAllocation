#!/usr/bin/python3
"""
Unit tests for security utilities
"""

import unittest
from unittest.mock import patch

from utils.security import (
    InputValidator,
    SecurityManager,
    get_secure_env_var,
    log_security_event,
)


class TestSecurityManager(unittest.TestCase):
    """SecurityManager 테스트"""

    def setUp(self):
        self.security_manager = SecurityManager()

    def test_generate_secret_key(self):
        """비밀 키 생성 테스트"""
        key = self.security_manager._generate_secret_key()
        self.assertIsInstance(key, str)
        self.assertGreater(len(key), 20)

    def test_hash_api_key(self):
        """API 키 해시화 테스트"""
        api_key = "test_api_key_123"
        hashed = self.security_manager.hash_api_key(api_key)

        self.assertIsInstance(hashed, str)
        self.assertEqual(len(hashed), 64)  # SHA256 hex length
        self.assertNotEqual(hashed, api_key)

        # 같은 키는 같은 해시를 생성해야 함
        hashed2 = self.security_manager.hash_api_key(api_key)
        self.assertEqual(hashed, hashed2)

    def test_validate_api_key_format_fred(self):
        """FRED API 키 형식 검증 테스트"""
        # 유효한 FRED API 키
        valid_key = "a" * 32
        self.assertTrue(
            self.security_manager.validate_api_key_format(valid_key, "fred")
        )

        # 유효하지 않은 키들
        invalid_keys = [
            "short",  # 너무 짧음
            "a" * 50,  # 너무 김
            "a" * 31 + "!",  # 잘못된 문자
            "",  # 빈 문자열
            None,  # None
        ]

        for invalid_key in invalid_keys:
            with self.subTest(key=invalid_key):
                self.assertFalse(
                    self.security_manager.validate_api_key_format(
                        invalid_key, "fred"
                    )
                )

    def test_validate_api_key_format_telegram(self):
        """Telegram API 키 형식 검증 테스트"""
        # 유효한 Telegram bot token
        valid_token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
        self.assertTrue(
            self.security_manager.validate_api_key_format(
                valid_token, "telegram"
            )
        )

        # 유효하지 않은 토큰들
        invalid_tokens = [
            "123456789",  # 콜론 없음
            "abc:def",  # 숫자가 아님
            "123456789:short",  # 너무 짧음
            "",  # 빈 문자열
            None,  # None
        ]

        for invalid_token in invalid_tokens:
            with self.subTest(token=invalid_token):
                self.assertFalse(
                    self.security_manager.validate_api_key_format(
                        invalid_token, "telegram"
                    )
                )

    def test_validate_chat_id(self):
        """Chat ID 검증 테스트"""
        # 유효한 Chat ID들
        valid_chat_ids = ["123456789", "@username", "987654321"]
        for chat_id in valid_chat_ids:
            with self.subTest(chat_id=chat_id):
                self.assertTrue(
                    self.security_manager.validate_chat_id(chat_id)
                )

        # 유효하지 않은 Chat ID들
        invalid_chat_ids = ["", None, "invalid@", "!@#$%"]
        for chat_id in invalid_chat_ids:
            with self.subTest(chat_id=chat_id):
                self.assertFalse(
                    self.security_manager.validate_chat_id(chat_id)
                )

    def test_sanitize_input(self):
        """입력 정리 테스트"""
        # 위험한 문자가 포함된 입력
        dangerous_input = "test<script>alert('xss')</script>"
        sanitized = self.security_manager.sanitize_input(dangerous_input)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertNotIn("(", sanitized)
        self.assertNotIn(")", sanitized)

        # 길이 제한 테스트
        long_input = "a" * 2000
        sanitized = self.security_manager.sanitize_input(
            long_input, max_length=100
        )
        self.assertEqual(len(sanitized), 100)

        # None 입력 처리
        sanitized = self.security_manager.sanitize_input(None)
        self.assertEqual(sanitized, "")

    def test_sanitize_input_preserve_linebreaks_for_telegram(self):
        """텔레그램용 sanitize에서 줄바꿈 보존 테스트"""
        input_message = "라인1\r\n라인2\t\t값\n\n\n  라인3  "
        sanitized = self.security_manager.sanitize_input(
            input_message,
            allow_html=True,
            preserve_linebreaks=True,
        )

        self.assertEqual(sanitized, "라인1\n라인2 값\n\n라인3")

    def test_sanitize_input_preserve_linebreaks_keeps_dangerous_char_filter(
        self,
    ):
        """줄바꿈 보존 옵션에서도 위험 문자 제거 유지 테스트"""
        input_message = "<b>Title</b>\nalert('x') | $HOME"
        sanitized = self.security_manager.sanitize_input(
            input_message,
            allow_html=True,
            preserve_linebreaks=True,
        )

        self.assertEqual(sanitized, "<b>Title</b>\nalert(x) HOME")

    def test_validate_ticker_symbol(self):
        """티커 심볼 검증 테스트"""
        # 유효한 티커들
        valid_tickers = ["SPY", "QQQ", "IEFA", "TLT", "VTI", "BND"]
        for ticker in valid_tickers:
            with self.subTest(ticker=ticker):
                self.assertTrue(
                    self.security_manager.validate_ticker_symbol(ticker)
                )

        # 유효하지 않은 티커들
        invalid_tickers = [
            "",
            None,
            "SPY!",
            "SPY@",
            "SPY\n",
            "SPY\t",
            "SPY SPY",
            "SPY@QQQ",
        ]
        for ticker in invalid_tickers:
            with self.subTest(ticker=ticker):
                self.assertFalse(
                    self.security_manager.validate_ticker_symbol(ticker)
                )

    def test_validate_ticker_list(self):
        """티커 목록 검증 테스트"""
        tickers = ["SPY", "QQQ", "INVALID!", "IEFA", "BAD@TICKER"]
        valid_tickers = self.security_manager.validate_ticker_list(tickers)

        self.assertEqual(valid_tickers, ["SPY", "QQQ", "IEFA"])
        self.assertEqual(len(valid_tickers), 3)

    def test_mask_sensitive_data(self):
        """민감한 데이터 마스킹 테스트"""
        # 정상적인 마스킹
        data = "1234567890"
        masked = self.security_manager.mask_sensitive_data(
            data, visible_chars=4
        )
        self.assertEqual(masked, "1234******")

        # 짧은 데이터
        short_data = "123"
        masked = self.security_manager.mask_sensitive_data(
            short_data, visible_chars=4
        )
        self.assertEqual(masked, "***")

        # 빈 데이터
        empty_data = ""
        masked = self.security_manager.mask_sensitive_data(empty_data)
        self.assertEqual(masked, "")

    def test_generate_secure_filename(self):
        """안전한 파일명 생성 테스트"""
        filename = self.security_manager.generate_secure_filename("test")
        self.assertTrue(filename.startswith("test_"))
        self.assertEqual(len(filename), len("test_") + 8)

        # 다른 파일명들은 다르어야 함
        filename2 = self.security_manager.generate_secure_filename("test")
        self.assertNotEqual(filename, filename2)


class TestInputValidator(unittest.TestCase):
    """InputValidator 테스트"""

    def test_validate_config_data(self):
        """설정 데이터 검증 테스트"""
        # 유효한 설정
        valid_config = {
            "FRED_API_KEY": "a" * 32,
            "TELEGRAM_BOT_TOKEN": (
                "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
            ),
            "TELEGRAM_CHAT_ID": "123456789",
        }
        errors = InputValidator.validate_config_data(valid_config)
        self.assertEqual(len(errors), 0)

        # 유효하지 않은 설정
        invalid_config = {
            "FRED_API_KEY": "short",
            "TELEGRAM_BOT_TOKEN": "invalid",
            "TELEGRAM_CHAT_ID": "invalid",
        }
        errors = InputValidator.validate_config_data(invalid_config)
        self.assertGreater(len(errors), 0)
        self.assertIn("Invalid FRED API key format", errors)
        self.assertIn("Invalid Telegram bot token format", errors)
        self.assertIn("Invalid Telegram chat ID format", errors)

    def test_validate_file_path(self):
        """파일 경로 검증 테스트"""
        # 유효한 경로들
        valid_paths = ["config.json", "data/file.txt", "subdir/config.json"]
        for path in valid_paths:
            with self.subTest(path=path):
                self.assertTrue(InputValidator.validate_file_path(path))

        # 유효하지 않은 경로들
        invalid_paths = [
            "../config.json",
            "~/file.txt",
            "$HOME/file.txt",
            "file;rm -rf /",
        ]
        for path in invalid_paths:
            with self.subTest(path=path):
                self.assertFalse(InputValidator.validate_file_path(path))


class TestSecurityUtilities(unittest.TestCase):
    """보안 유틸리티 함수 테스트"""

    @patch.dict("os.environ", {"TEST_VAR": "test_value"})
    def test_get_secure_env_var(self):
        """안전한 환경변수 가져오기 테스트"""
        value = get_secure_env_var("TEST_VAR")
        self.assertEqual(value, "test_value")

        # 존재하지 않는 환경변수
        value = get_secure_env_var("NON_EXISTENT", "default")
        self.assertEqual(value, "default")

    def test_log_security_event(self):
        """보안 이벤트 로깅 테스트"""
        # 로깅이 예외 없이 실행되는지 확인
        try:
            log_security_event("TEST_EVENT", "Test details")
            log_security_event("WARNING_EVENT", "Warning details", "WARNING")
            log_security_event("ERROR_EVENT", "Error details", "ERROR")
        except Exception as e:
            self.fail(f"log_security_event raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
