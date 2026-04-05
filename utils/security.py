#!/usr/bin/python3
"""
Security utilities for API key management and input validation
"""

import hashlib
import hmac
import logging
import os
import re
import secrets
import string
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class SecurityManager:
    """보안 관리 클래스"""

    def __init__(self, secret_key: Optional[str] = None):
        """
        보안 관리자를 초기화합니다.

        Args:
            secret_key: 암호화에 사용할 비밀 키 (기본값: 랜덤 생성)
        """
        self.secret_key = secret_key or self._generate_secret_key()
        LOGGER.debug("Security manager initialized")

    def _generate_secret_key(self) -> str:
        """안전한 비밀 키를 생성합니다."""
        return secrets.token_urlsafe(32)

    def hash_api_key(self, api_key: str) -> str:
        """
        API 키를 해시화합니다.

        Args:
            api_key: 원본 API 키

        Returns:
            해시화된 API 키
        """
        return hmac.new(
            self.secret_key.encode(), api_key.encode(), hashlib.sha256
        ).hexdigest()

    def validate_api_key_format(self, api_key: str, key_type: str) -> bool:
        """
        API 키 형식을 검증합니다.

        Args:
            api_key: 검증할 API 키
            key_type: 키 타입 (fred, telegram)

        Returns:
            유효성 여부
        """
        if not api_key or not isinstance(api_key, str):
            return False

        # 기본 길이 검증
        if len(api_key) < 10:
            LOGGER.warning(f"{key_type} API key too short")
            return False

        if len(api_key) > 200:
            LOGGER.warning(f"{key_type} API key too long")
            return False

        # FRED API 키 형식 검증
        if key_type == "fred":
            # FRED API 키는 보통 32자리 영숫자
            if not re.match(r"^[a-zA-Z0-9]{32}$", api_key):
                LOGGER.warning("Invalid FRED API key format")
                return False

        # Telegram Bot Token 형식 검증
        elif key_type == "telegram":
            # Telegram bot token 형식: 숫자:문자열
            if not re.match(r"^\d+:[a-zA-Z0-9_-]{35}$", api_key):
                LOGGER.warning("Invalid Telegram bot token format")
                return False

        return True

    def validate_chat_id(self, chat_id: str) -> bool:
        """
        Telegram Chat ID를 검증합니다.

        Args:
            chat_id: 검증할 Chat ID

        Returns:
            유효성 여부
        """
        if not chat_id or not isinstance(chat_id, str):
            return False

        # Chat ID는 숫자이거나 @username 형식
        if not (chat_id.isdigit() or chat_id.startswith("@")):
            LOGGER.warning("Invalid Telegram chat ID format")
            return False

        return True

    def sanitize_input(
        self,
        input_string: str,
        max_length: int = 1000,
        allow_html: bool = False,
        preserve_linebreaks: bool = False,
    ) -> str:
        """
        사용자 입력을 정리합니다.

        Args:
            input_string: 정리할 입력 문자열
            max_length: 최대 길이
            allow_html: HTML 태그 허용 여부
            preserve_linebreaks: 줄바꿈 보존 여부

        Returns:
            정리된 문자열
        """
        if not isinstance(input_string, str):
            return ""

        # 길이 제한
        sanitized = input_string[:max_length]

        # 위험한 문자 제거 (HTML 허용 시 제외)
        if not allow_html:
            dangerous_chars = [
                "<",
                ">",
                '"',
                "'",
                "&",
                ";",
                "(",
                ")",
                "|",
                "`",
                "$",
            ]
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, "")
        else:
            # HTML 허용 시 위험한 문자만 제거 (HTML 태그는 보존)
            dangerous_chars = [
                '"',
                "'",
                ";",
                "|",
                "`",
                "$",
            ]
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, "")

        if preserve_linebreaks:
            # 줄바꿈은 유지하고, 탭/연속 공백만 정리
            sanitized = sanitized.replace("\r\n", "\n").replace("\r", "\n")
            sanitized = re.sub(r"[ \t]+", " ", sanitized)
            sanitized = "\n".join(line.strip() for line in sanitized.split("\n"))
            # 과도한 빈 줄은 최대 2개 줄바꿈(빈 줄 1개)으로 제한
            sanitized = re.sub(r"\n{3,}", "\n\n", sanitized).strip()
        else:
            # 연속된 공백 제거
            sanitized = re.sub(r"\s+", " ", sanitized).strip()

        return sanitized

    def validate_ticker_symbol(self, ticker: str) -> bool:
        """
        티커 심볼을 검증합니다.

        Args:
            ticker: 검증할 티커 심볼

        Returns:
            유효성 여부
        """
        if not ticker or not isinstance(ticker, str):
            return False

        # 원본 문자열에 공백이나 제어 문자가 포함되어 있으면 무효
        if re.search(r"[\s\n\r\t]", ticker):
            LOGGER.warning(
                f"Invalid ticker symbol format (contains whitespace): "
                f"{repr(ticker)}"
            )
            return False

        # 티커 심볼은 1-10자리 영숫자와 일부 특수문자만 허용
        if not re.match(r"^[A-Za-z0-9.-]{1,10}$", ticker):
            LOGGER.warning(f"Invalid ticker symbol format: {ticker}")
            return False

        return True

    def validate_ticker_list(self, tickers: List[str]) -> List[str]:
        """
        티커 목록을 검증하고 정리합니다.

        Args:
            tickers: 검증할 티커 목록

        Returns:
            유효한 티커 목록
        """
        if not isinstance(tickers, list):
            return []

        valid_tickers = []
        for ticker in tickers:
            if self.validate_ticker_symbol(ticker):
                valid_tickers.append(ticker.upper())
            else:
                LOGGER.warning(f"Skipping invalid ticker: {ticker}")

        return valid_tickers

    def mask_sensitive_data(self, data: str, visible_chars: int = 4) -> str:
        """
        민감한 데이터를 마스킹합니다.

        Args:
            data: 마스킹할 데이터
            visible_chars: 보여줄 문자 수

        Returns:
            마스킹된 데이터
        """
        if not data or len(data) <= visible_chars:
            return "*" * len(data) if data else ""

        return data[:visible_chars] + "*" * (len(data) - visible_chars)

    def generate_secure_filename(self, prefix: str = "file") -> str:
        """
        안전한 파일명을 생성합니다.

        Args:
            prefix: 파일명 접두사

        Returns:
            안전한 파일명
        """
        random_suffix = "".join(
            secrets.choice(string.ascii_lowercase + string.digits)
            for _ in range(8)
        )
        return f"{prefix}_{random_suffix}"


class InputValidator:
    """입력 검증 클래스"""

    @staticmethod
    def validate_config_data(config_data: Dict[str, Any]) -> List[str]:
        """
        설정 데이터를 검증합니다.

        Args:
            config_data: 검증할 설정 데이터

        Returns:
            오류 메시지 목록
        """
        errors = []

        # 필수 키 검증
        required_keys = [
            "FRED_API_KEY",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
        ]
        for key in required_keys:
            if key not in config_data or not config_data[key]:
                errors.append(f"Missing required configuration: {key}")

        # API 키 형식 검증
        security_manager = SecurityManager()

        if "FRED_API_KEY" in config_data:
            if not security_manager.validate_api_key_format(
                config_data["FRED_API_KEY"], "fred"
            ):
                errors.append("Invalid FRED API key format")

        if "TELEGRAM_BOT_TOKEN" in config_data:
            if not security_manager.validate_api_key_format(
                config_data["TELEGRAM_BOT_TOKEN"], "telegram"
            ):
                errors.append("Invalid Telegram bot token format")

        if "TELEGRAM_CHAT_ID" in config_data:
            if not security_manager.validate_chat_id(
                config_data["TELEGRAM_CHAT_ID"]
            ):
                errors.append("Invalid Telegram chat ID format")

        return errors

    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """
        파일 경로를 검증합니다.

        Args:
            file_path: 검증할 파일 경로

        Returns:
            유효성 여부
        """
        if not file_path or not isinstance(file_path, str):
            return False

        # 경로 주입 공격 방지
        dangerous_patterns = ["..", "~", "$", "`", ";", "|", "&"]
        for pattern in dangerous_patterns:
            if pattern in file_path:
                LOGGER.warning(
                    f"Potentially dangerous path pattern: {pattern}"
                )
                return False

        # 절대 경로가 아닌 경우만 허용
        if os.path.isabs(file_path) and not file_path.startswith(os.getcwd()):
            LOGGER.warning(
                "Absolute path outside current directory not allowed"
            )
            return False

        return True


def get_secure_env_var(
    var_name: str, default: Optional[str] = None
) -> Optional[str]:
    """
    환경변수를 안전하게 가져옵니다.

    Args:
        var_name: 환경변수 이름
        default: 기본값

    Returns:
        환경변수 값 또는 기본값
    """
    value = os.getenv(var_name, default)

    if value and len(value) > 1000:
        LOGGER.warning(f"Environment variable {var_name} is unusually long")

    return value


def log_security_event(
    event_type: str, details: str, level: str = "INFO"
) -> None:
    """
    보안 이벤트를 로깅합니다.

    Args:
        event_type: 이벤트 타입
        details: 이벤트 세부사항
        level: 로그 레벨
    """
    log_message = f"SECURITY_EVENT: {event_type} - {details}"

    if level.upper() == "WARNING":
        LOGGER.warning(log_message)
    elif level.upper() == "ERROR":
        LOGGER.error(log_message)
    else:
        LOGGER.info(log_message)
