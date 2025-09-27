#!/usr/bin/python3
"""
Centralized logging configuration for asset allocation system
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from config import API_CONFIG


class LoggingConfig:
    """중앙화된 로깅 설정 클래스"""

    # 로깅 레벨 상수
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    # 로깅 포맷 상수
    DETAILED_FORMAT = (
        "%(asctime)s | %(name)s | %(levelname)s | "
        "%(funcName)s:%(lineno)d | %(message)s"
    )
    SIMPLE_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
    JSON_FORMAT = (
        '{"timestamp": "%(asctime)s", "logger": "%(name)s", '
        '"level": "%(levelname)s", "function": "%(funcName)s", '
        '"line": %(lineno)d, "message": "%(message)s"}'
    )

    @staticmethod
    def setup_logging(
        log_level: str = "INFO",
        log_format: str = "detailed",
        log_file: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        disable_utils_logs: bool = True,
    ) -> None:
        """
        로깅 시스템을 설정합니다.

        Args:
            log_level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: 로그 포맷 (detailed, simple, json)
            log_file: 로그 파일 경로 (None이면 콘솔만)
            max_file_size: 로그 파일 최대 크기 (바이트)
            backup_count: 백업 파일 개수
            disable_utils_logs: utils 모듈 로그 비활성화 여부
        """
        # 로깅 레벨 설정
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {log_level}")

        # 포맷 설정
        format_map = {
            "detailed": LoggingConfig.DETAILED_FORMAT,
            "simple": LoggingConfig.SIMPLE_FORMAT,
            "json": LoggingConfig.JSON_FORMAT,
        }
        log_format_str = format_map.get(
            log_format, LoggingConfig.DETAILED_FORMAT
        )

        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # 기존 핸들러 제거
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(log_format_str)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # 파일 핸들러 설정 (선택적)
        if log_file:
            # 로그 디렉토리 생성
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # 로테이팅 파일 핸들러
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(numeric_level)
            file_formatter = logging.Formatter(log_format_str)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        # 특정 라이브러리 로깅 레벨 조정
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("yfinance").setLevel(logging.WARNING)

        # utils 모듈 로깅 레벨 설정
        if disable_utils_logs:
            logging.getLogger("utils").setLevel(logging.WARNING)
        else:
            # 환경변수로 제어 가능
            utils_log_level = os.getenv("UTILS_LOG_LEVEL", log_level)
            utils_numeric_level = getattr(
                logging, utils_log_level.upper(), logging.INFO
            )
            logging.getLogger("utils").setLevel(utils_numeric_level)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        모듈별 로거를 가져옵니다.

        Args:
            name: 로거 이름 (보통 __name__)

        Returns:
            설정된 로거 인스턴스
        """
        return logging.getLogger(name)

    @staticmethod
    def log_strategy_start(logger: logging.Logger, strategy_name: str) -> None:
        """전략 시작 로깅"""
        logger.info(f"🚀 Starting {strategy_name} strategy execution")

    @staticmethod
    def log_strategy_success(
        logger: logging.Logger, strategy_name: str
    ) -> None:
        """전략 성공 로깅"""
        logger.info(f"✅ {strategy_name} strategy executed successfully")

    @staticmethod
    def log_strategy_failure(
        logger: logging.Logger, strategy_name: str, error: str
    ) -> None:
        """전략 실패 로깅"""
        logger.error(f"❌ {strategy_name} strategy failed: {error}")

    @staticmethod
    def log_data_retrieval(
        logger: logging.Logger,
        source: str,
        tickers: list,
        cached: bool = False,
    ) -> None:
        """데이터 조회 로깅"""
        cache_status = "cached" if cached else "fresh"
        ticker_display = f"{tickers[:5]}{'...' if len(tickers) > 5 else ''}"
        logger.info(
            f"📊 Retrieved {cache_status} data from {source} for "
            f"{len(tickers)} tickers: {ticker_display}"
        )

    @staticmethod
    def log_allocation_result(
        logger: logging.Logger, strategy_name: str, allocation: dict
    ) -> None:
        """배분 결과 로깅"""
        total = sum(allocation.values())
        logger.info(
            f"💰 {strategy_name} allocation: {allocation} (Total: {total:.1f}%)"
        )

    @staticmethod
    def log_performance(
        logger: logging.Logger,
        operation: str,
        duration: float,
        success: bool = True,
    ) -> None:
        """성능 로깅"""
        status = "✅" if success else "❌"
        logger.debug(f"{status} {operation} completed in {duration:.3f}s")

    @staticmethod
    def log_security_event(
        logger: logging.Logger,
        event_type: str,
        details: str,
        level: str = "WARNING",
    ) -> None:
        """보안 이벤트 로깅"""
        log_level = getattr(logging, level.upper(), logging.WARNING)
        logger.log(log_level, f"🔒 Security Event [{event_type}]: {details}")

    @staticmethod
    def log_error_with_context(
        logger: logging.Logger,
        error: Exception,
        context: str,
        additional_info: Optional[dict] = None,
    ) -> None:
        """컨텍스트가 포함된 에러 로깅"""
        error_msg = f"💥 Error in {context}: {str(error)}"
        if additional_info:
            error_msg += f" | Context: {additional_info}"
        logger.error(error_msg, exc_info=True)


def setup_default_logging() -> None:
    """기본 로깅 설정을 적용합니다."""
    # 환경변수에서 로깅 설정 읽기
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "detailed")
    log_file = os.getenv("LOG_FILE", "logs/asset_allocation.log")

    LoggingConfig.setup_logging(
        log_level=log_level,
        log_format=log_format,
        log_file=log_file,
    )


# 전역 로깅 설정 적용
setup_default_logging()
