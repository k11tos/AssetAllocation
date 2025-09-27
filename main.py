#!/usr/bin/python3
"""
Get portfolio with original dual momentum, VAA and LAA
"""

import datetime
import json
import logging
import sys
from typing import Dict, List, Optional

from config import STRATEGY_CONFIG, validate_config
from exceptions import (
    DataRetrievalError,
    DataValidationError,
    NetworkError,
    StrategyExecutionError,
)
from portfolio import (
    get_financial_data,
    get_hybrid_asset_allocation,
    get_korean_all_weather_allocation,
    print_info_message,
)
from utils.logging_config import LoggingConfig
from utils.performance_monitor import get_performance_monitor
from utils.strategy_optimizer import get_required_tickers_for_strategy

# 로깅 설정
LOGGER = LoggingConfig.get_logger(__name__)


def load_tickers(file_path: Optional[str] = None) -> List[str]:
    """ETF 티커 목록을 로드합니다."""
    if file_path is None:
        file_path = STRATEGY_CONFIG.TICKER_FILE

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            tickers = json.load(file)

        if not tickers:
            raise ValueError(f"No tickers found in {file_path}")

        LOGGER.info(
            f"📋 Successfully loaded {len(tickers)} tickers from {file_path}"
        )
        return tickers

    except FileNotFoundError:
        LoggingConfig.log_error_with_context(
            LOGGER,
            FileNotFoundError(f"Ticker file not found: {file_path}"),
            "load_tickers",
        )
        raise
    except json.JSONDecodeError as e:
        LoggingConfig.log_error_with_context(
            LOGGER, e, "load_tickers", {"file_path": file_path}
        )
        raise
    except Exception as e:
        LoggingConfig.log_error_with_context(
            LOGGER, e, "load_tickers", {"file_path": file_path}
        )
        raise


def execute_haa_strategy(tickers: list) -> Optional[Dict[str, float]]:
    """HAA 전략을 최적화된 데이터로 실행합니다."""
    try:
        LoggingConfig.log_strategy_start(LOGGER, "HAA")

        # HAA 전략에 필요한 티커만 추출
        required_tickers = get_required_tickers_for_strategy("haa")
        LOGGER.info(f"🔍 HAA 전략: {len(required_tickers)}개 자산 데이터 요청")

        (
            momentum_score,
            momentum_score_simple,
            profit_12month,
            profit_6month,
            sma_12month,
            today_price,
        ) = get_financial_data(" ".join(required_tickers))

        haa = get_hybrid_asset_allocation(momentum_score_simple)
        LoggingConfig.log_strategy_success(LOGGER, "HAA")
        LoggingConfig.log_allocation_result(LOGGER, "HAA", haa)
        return haa

    except DataValidationError as e:
        LoggingConfig.log_strategy_failure(
            LOGGER, "HAA", f"Data validation failed: {str(e)}"
        )
        return None
    except DataRetrievalError as e:
        LoggingConfig.log_strategy_failure(
            LOGGER, "HAA", f"Data retrieval failed: {str(e)}"
        )
        return None
    except NetworkError as e:
        LoggingConfig.log_strategy_failure(
            LOGGER, "HAA", f"Network error: {str(e)}"
        )
        return None
    except StrategyExecutionError as e:
        LoggingConfig.log_strategy_failure(
            LOGGER, "HAA", f"Execution failed: {str(e)}"
        )
        return None
    except Exception as e:
        LoggingConfig.log_error_with_context(LOGGER, e, "HAA strategy")
        return None


def main() -> None:
    """
    Main function
    :return: None
    """
    # 설정 검증
    if not validate_config():
        LOGGER.error("❌ Configuration validation failed")
        sys.exit(1)

    LOGGER.info("🚀 Starting asset allocation process...")

    total_number_of_strategy = STRATEGY_CONFIG.TOTAL_STRATEGIES
    successful_strategies = 0

    try:
        # 티커 로드
        tickers = load_tickers()
        etf_descriptions = {ticker: ticker for ticker in tickers}

        # 현재 날짜 출력
        current_date = datetime.datetime.today().date()
        print_info_message(f"Asset Allocation Report - {current_date}")
        LOGGER.info(f"📅 Processing date: {current_date}")

        # HAA 전략 실행
        haa_result = execute_haa_strategy(tickers)
        if haa_result:
            print_asset_allocation(
                haa_result, etf_descriptions, total_number_of_strategy, "[HAA]"
            )
            successful_strategies += 1
        else:
            LOGGER.warning("⚠️ HAA strategy failed - skipping output")

        # 한국형 올웨더 전략 (항상 실행)
        try:
            LoggingConfig.log_strategy_start(LOGGER, "Korean All-Weather")
            korean_all_weather = get_korean_all_weather_allocation()
            print_asset_allocation(
                korean_all_weather, None, total_number_of_strategy, "[KAW]"
            )
            successful_strategies += 1
            LoggingConfig.log_strategy_success(LOGGER, "Korean All-Weather")
            LoggingConfig.log_allocation_result(
                LOGGER, "Korean All-Weather", korean_all_weather
            )
        except StrategyExecutionError as e:
            LoggingConfig.log_strategy_failure(
                LOGGER, "Korean All-Weather", f"Execution failed: {str(e)}"
            )
        except Exception as e:
            LoggingConfig.log_error_with_context(
                LOGGER, e, "Korean All-Weather strategy"
            )

        # 실행 결과 요약
        LOGGER.info(
            f"✅ Asset allocation process completed. "
            f"{successful_strategies}/{total_number_of_strategy} "
            f"strategies executed successfully"
        )

        # 성능 모니터링 결과 출력
        performance_monitor = get_performance_monitor()
        performance_monitor.log_summary()

        if successful_strategies == 0:
            LOGGER.error(
                "❌ All strategies failed - no allocation recommendations "
                "generated"
            )
            sys.exit(1)

    except Exception as e:
        LoggingConfig.log_error_with_context(LOGGER, e, "main process")
        sys.exit(1)


def print_asset_allocation(
    asset_allocation: Dict[str, float],
    etf_descriptions: Dict[str, str],
    total_number_of_strategy: int,
    strategy_name: str,
) -> None:
    """
    Print asset allocation results
    :param asset_allocation: Dictionary with asset allocation
    :param etf_descriptions: Dictionary mapping tickers to descriptions
    :param total_number_of_strategy: Total number of strategies
    :param strategy_name: Name of the strategy
    :return: None
    """
    if etf_descriptions is not None:
        for key, value in asset_allocation.items():
            print_info_message(
                f"{strategy_name} {etf_descriptions[key]}: "
                f"{round(value / total_number_of_strategy, 2)} %"
            )
    else:
        for key, value in asset_allocation.items():
            print_info_message(
                f"{strategy_name} {key}: "
                f"{round(value / total_number_of_strategy, 2)} %"
            )


if __name__ == "__main__":
    main()
