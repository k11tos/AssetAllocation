#!/usr/bin/python3
"""
Communication service for messaging and notifications
"""

import asyncio
import logging
from typing import Dict, Optional

import requests
import telegram
from requests.adapters import HTTPAdapter
from telegram.ext import Updater
from urllib3.util.retry import Retry

from config import API_CONFIG
from utils.logging_config import LoggingConfig
from utils.security import InputValidator, SecurityManager, log_security_event

LOGGER = LoggingConfig.get_logger(__name__)


class CommunicationService:
    """통신 서비스 (텔레그램 등)"""

    def __init__(self):
        self.telegram_account = None
        self.security_manager = SecurityManager()
        self._initialize_telegram()
        self._setup_session()

    def _initialize_telegram(self) -> None:
        """텔레그램 계정을 초기화합니다."""
        try:
            api_token = API_CONFIG.TELEGRAM_BOT_TOKEN
            chat_id = API_CONFIG.TELEGRAM_CHAT_ID

            # Fallback to portfolio.txt if environment variables are not set
            if not api_token or not chat_id:
                try:
                    if not InputValidator.validate_file_path(
                        API_CONFIG.FALLBACK_FILE
                    ):
                        raise ValueError("Invalid fallback file path")

                    with open(
                        API_CONFIG.FALLBACK_FILE, encoding="utf-8"
                    ) as file_descriptor:
                        lines = file_descriptor.readlines()
                        api_token = lines[1].strip()
                        chat_id = lines[2].strip()
                except (FileNotFoundError, IndexError):
                    LOGGER.error(
                        f"Neither environment variables nor "
                        f"{API_CONFIG.FALLBACK_FILE} file "
                        "found for Telegram configuration."
                    )
                    raise

            # API 키 및 Chat ID 검증
            if not self.security_manager.validate_api_key_format(
                api_token, "telegram"
            ):
                log_security_event(
                    "INVALID_API_KEY",
                    "Invalid Telegram bot token format",
                    "ERROR",
                )
                raise ValueError("Invalid Telegram bot token format")

            if not self.security_manager.validate_chat_id(chat_id):
                log_security_event(
                    "INVALID_CHAT_ID",
                    "Invalid Telegram chat ID format",
                    "ERROR",
                )
                raise ValueError("Invalid Telegram chat ID format")

            self.telegram_account = {
                "bot": telegram.Bot(api_token),
                "chat_id": chat_id,
            }
            LOGGER.debug("📱 Telegram API initialized successfully")
            log_security_event(
                "API_INITIALIZED", "Telegram API initialized successfully"
            )

        except Exception as e:
            LOGGER.error(f"Failed to initialize Telegram account: {str(e)}")
            log_security_event(
                "API_INIT_FAILED",
                f"Telegram API initialization failed: {str(e)}",
                "ERROR",
            )
            raise

    def _setup_session(self) -> None:
        """HTTP 세션을 설정합니다."""
        self.session = requests.Session()

        # 재시도 전략 설정
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def send_message(self, message: str) -> bool:
        """
        텔레그램으로 메시지를 전송합니다.

        Args:
            message: 전송할 메시지

        Returns:
            전송 성공 여부
        """
        if self.telegram_account is None:
            LOGGER.warning(
                "⚠️ Telegram not initialized, logging message instead"
            )
            LOGGER.info(f"📝 {message}")
            return False

        # 메시지 검증 및 정리
        if not message or not isinstance(message, str):
            LOGGER.warning("⚠️ Invalid message format")
            return False

        # HTML 태그를 보존하면서 sanitize
        sanitized_message = self.security_manager.sanitize_input(
            message, max_length=4000, allow_html=True
        )
        if not sanitized_message:
            LOGGER.warning("⚠️ Message sanitization resulted in empty message")
            return False

        try:
            # 동기 방식으로 메시지 전송 (requests 사용)
            bot_token = self.telegram_account["bot"].token
            chat_id = self.telegram_account["chat_id"]

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": sanitized_message,
                "parse_mode": None,
            }

            headers = {"User-Agent": "AssetAllocationBot/1.0"}

            response = self.session.post(
                url, data=data, headers=headers, timeout=30
            )
            response.raise_for_status()

            LOGGER.debug(
                f"📤 Message sent successfully: {sanitized_message[:50]}..."
            )
            log_security_event(
                "MESSAGE_SENT",
                f"Message sent via Telegram: {len(sanitized_message)} chars",
            )
            return True

        except Exception as error:
            LOGGER.error(f"Failed to send Telegram message: {str(error)}")
            log_security_event(
                "MESSAGE_FAILED",
                f"Failed to send message: {str(error)}",
                "ERROR",
            )
            return False

    def get_telegram_bot(
        self, mode: str = "information"
    ) -> Optional[telegram.Bot]:
        """
        텔레그램 봇 인스턴스를 반환합니다.

        Args:
            mode: 봇 모드 ("information" 또는 "conversation")

        Returns:
            텔레그램 봇 인스턴스 또는 None
        """
        if self.telegram_account is None:
            return None

        try:
            if mode == "information":
                return self.telegram_account["bot"]
            elif mode == "conversation":
                return Updater(
                    token=self.telegram_account["bot"].token, use_context=True
                )
            else:
                LOGGER.error(f"Invalid mode for telegram bot: {mode}")
                return None

        except Exception as e:
            LOGGER.error(f"Failed to get telegram bot: {str(e)}")
            return None
