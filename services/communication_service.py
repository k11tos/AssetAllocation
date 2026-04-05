#!/usr/bin/python3
"""
Communication service for messaging and notifications
"""

import logging
from typing import Optional, Sequence, Union

import requests
import telegram
from requests.adapters import HTTPAdapter
from telegram import Bot
from telegram.ext import Application
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

    @staticmethod
    def _message_preview(message: str, max_length: int = 80) -> str:
        """로그 출력용 안전한 메시지 미리보기 문자열을 반환합니다."""
        normalized = message.replace("\n", "\\n")
        if len(normalized) <= max_length:
            return normalized
        return f"{normalized[:max_length]}..."

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
            message_thread_id = API_CONFIG.TELEGRAM_MESSAGE_THREAD_ID or None

            LOGGER.debug(
                "📨 Telegram send attempt payload_type=single "
                "total_messages=1 message_index=1/1 chat_id=%s "
                "message_thread_id=%s preview='%s'",
                chat_id,
                message_thread_id,
                self._message_preview(sanitized_message),
            )

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": sanitized_message,
                "parse_mode": None,
            }
            if message_thread_id is not None:
                data["message_thread_id"] = message_thread_id

            headers = {"User-Agent": "AssetAllocationBot/1.0"}

            response = self.session.post(
                url, data=data, headers=headers, timeout=30
            )
            response.raise_for_status()
            response_payload = response.json()
            result_payload = response_payload.get("result", {})
            result_chat = result_payload.get("chat", {})

            LOGGER.debug(
                "📤 Telegram send success message_id=%s chat.id=%s "
                "chat.type=%s",
                result_payload.get("message_id"),
                result_chat.get("id"),
                result_chat.get("type"),
            )
            log_security_event(
                "MESSAGE_SENT",
                f"Message sent via Telegram: {len(sanitized_message)} chars",
            )
            return True

        except Exception as error:
            LOGGER.exception(
                "Failed to send Telegram message chat_id=%s "
                "message_thread_id=%s preview='%s'",
                self.telegram_account.get("chat_id"),
                API_CONFIG.TELEGRAM_MESSAGE_THREAD_ID or None,
                self._message_preview(sanitized_message),
            )
            log_security_event(
                "MESSAGE_FAILED",
                f"Failed to send message: {str(error)}",
                "ERROR",
            )
            return False

    def send_messages(self, messages: Sequence[str]) -> bool:
        """Send multiple Telegram messages in order.

        Fail-fast semantics prevent confusing partial report delivery.
        """
        if not isinstance(messages, Sequence) or isinstance(messages, str):
            LOGGER.warning("⚠️ Invalid messages payload format")
            return False

        if not messages:
            LOGGER.warning("⚠️ Empty messages payload")
            return False

        total_messages = len(messages)
        chat_id = (
            self.telegram_account.get("chat_id")
            if self.telegram_account is not None
            else None
        )
        message_thread_id = API_CONFIG.TELEGRAM_MESSAGE_THREAD_ID or None

        for index, message in enumerate(messages, start=1):
            if not isinstance(message, str) or not message:
                LOGGER.warning(
                    "⚠️ Invalid message item at index=%s/%s type=%s",
                    index,
                    total_messages,
                    type(message).__name__,
                )
                return False

            LOGGER.debug(
                "📨 Telegram send attempt payload_type=list "
                "total_messages=%s message_index=%s/%s chat_id=%s "
                "message_thread_id=%s preview='%s'",
                total_messages,
                index,
                total_messages,
                chat_id,
                message_thread_id,
                self._message_preview(message),
            )
            try:
                if not self.send_message(message):
                    LOGGER.error(
                        "Telegram multi-send failed at message_index=%s/%s",
                        index,
                        total_messages,
                    )
                    return False
            except Exception:
                LOGGER.exception(
                    "Telegram multi-send raised at message_index=%s/%s",
                    index,
                    total_messages,
                )
                raise
        return True

    def get_telegram_bot(
        self, mode: str = "information"
    ) -> Optional[Union[telegram.Bot, Application]]:
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
                # python-telegram-bot 22.3+에서는 Application.builder() 사용
                return (
                    Application.builder()
                    .token(self.telegram_account["bot"].token)
                    .build()
                )
            else:
                LOGGER.error(f"Invalid mode for telegram bot: {mode}")
                return None

        except Exception as e:
            LOGGER.error(f"Failed to get telegram bot: {str(e)}")
            return None
