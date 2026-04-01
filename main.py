#!/usr/bin/python3
"""
Get portfolio with original dual momentum, VAA and LAA
"""

import json
import os
import sys
from typing import Dict, List, Optional

from config import STRATEGY_CONFIG, validate_config
from execution_output import (
    format_compact_execution_diff_summary,
    format_execution_diff_summary,
    get_execution_now,
    load_execution_output_json,
    save_execution_output_json,
)
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
from strategy_runner import run_selected_strategies
from utils.logging_config import LoggingConfig
from utils.performance_monitor import get_performance_monitor
from utils.strategy_optimizer import get_required_tickers_for_strategy

# 로깅 설정
LOGGER = LoggingConfig.get_logger(__name__)
SCHEDULED_OUTPUT_DIR = "outputs"
SCHEDULED_LATEST_RESULT_PATH = os.path.join(SCHEDULED_OUTPUT_DIR, "latest.json")
SCHEDULED_HISTORY_DIR = os.path.join(SCHEDULED_OUTPUT_DIR, "history")


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
            "📋 Successfully loaded %d tickers from %s", len(tickers), file_path
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


def execute_haa_strategy() -> Optional[Dict[str, float]]:
    """HAA 전략을 최적화된 데이터로 실행합니다."""
    try:
        LoggingConfig.log_strategy_start(LOGGER, "HAA")

        # HAA 전략에 필요한 티커만 추출
        required_tickers = get_required_tickers_for_strategy("haa")
        LOGGER.info("🔍 HAA 전략: %d개 자산 데이터 요청", len(required_tickers))

        (
            _,
            momentum_score_simple,
            _,
            _,
            _,
            _,
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


def execute_kaw_strategy() -> Optional[Dict[str, float]]:
    """한국형 올웨더 전략을 실행합니다."""
    try:
        LoggingConfig.log_strategy_start(LOGGER, "Korean All-Weather")
        korean_all_weather = get_korean_all_weather_allocation()
        LoggingConfig.log_strategy_success(LOGGER, "Korean All-Weather")
        LoggingConfig.log_allocation_result(
            LOGGER, "Korean All-Weather", korean_all_weather
        )
        return korean_all_weather
    except StrategyExecutionError as e:
        LoggingConfig.log_strategy_failure(
            LOGGER, "Korean All-Weather", f"Execution failed: {str(e)}"
        )
        return None
    except Exception as e:
        LoggingConfig.log_error_with_context(
            LOGGER, e, "Korean All-Weather strategy"
        )
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
        current_date = get_execution_now().date()
        formatted_date = current_date.strftime("%Y년 %m월 %d일")
        weekday = current_date.strftime("%A")

        # 헤더 메시지를 개별 메시지로 분할
        print_info_message("자산 배분 리포트")
        print_info_message(f"{formatted_date} ({weekday})")
        LOGGER.info("📅 Processing date: %s", current_date)

        strategy_results = run_selected_strategies(["HAA", "KAW"], "main")

        # HAA 전략 실행
        haa_result = strategy_results["HAA"]
        if haa_result:
            print_asset_allocation(
                haa_result, etf_descriptions, total_number_of_strategy, "[HAA]"
            )
            successful_strategies += 1
        else:
            LOGGER.warning("⚠️ HAA strategy failed - skipping output")

        # 한국형 올웨더 전략 (항상 실행)
        kaw_result = strategy_results["KAW"]
        if kaw_result:
            print_asset_allocation(
                kaw_result, None, total_number_of_strategy, "[KAW]"
            )
            successful_strategies += 1
        else:
            LOGGER.warning("⚠️ KAW strategy failed - skipping output")

        # 실행 결과 요약
        success_rate = (successful_strategies / total_number_of_strategy) * 100

        # 요약 메시지 단순화
        success_message = (
            f"성공률: {success_rate:.1f}% "
            f"({successful_strategies}/{total_number_of_strategy})"
        )
        print_info_message(success_message)

        LOGGER.info(
            "✅ Asset allocation process completed. "
            "%d/%d strategies executed successfully",
            successful_strategies,
            total_number_of_strategy,
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

        persist_scheduled_execution_result(strategy_results)

    except Exception as e:
        LoggingConfig.log_error_with_context(LOGGER, e, "main process")
        sys.exit(1)


def persist_scheduled_execution_result(
    strategy_results: Dict[str, Optional[Dict[str, float]]],
) -> None:
    """Save scheduled execution results and compare with previous snapshot."""
    stage_overrides = {
        "snapshot_save": {"status": "success"},
        "notification_reporting": {
            "status": "skipped",
            "detail": "No previous snapshot available for diff reporting",
        },
    }
    previous_result_data = None
    try:
        previous_result_data = load_execution_output_json(
            SCHEDULED_LATEST_RESULT_PATH
        )
    except FileNotFoundError:
        LOGGER.info(
            "ℹ️ No previous scheduled execution snapshot at %s",
            SCHEDULED_LATEST_RESULT_PATH,
        )
    except Exception as e:
        LOGGER.warning(
            "⚠️ Failed to load previous scheduled snapshot: %s",
            e,
        )

    if previous_result_data is not None:
        try:
            diff_summary = format_execution_diff_summary(
                previous_result_data, strategy_results
            )
            LOGGER.info("📊 Scheduled execution diff summary:\n%s", diff_summary)

            compact_summary = format_compact_execution_diff_summary(
                previous_result_data, strategy_results
            )
            if compact_summary:
                print_info_message(compact_summary)
            stage_overrides["notification_reporting"] = {"status": "success"}
        except Exception as e:
            stage_overrides["notification_reporting"] = {
                "status": "failure",
                "error": str(e),
            }
            LOGGER.warning(
                "⚠️ Failed to format scheduled execution diff summary: %s",
                e,
            )

    history_file_path = os.path.join(
        SCHEDULED_HISTORY_DIR,
        f"{get_execution_now().strftime('%Y%m%d_%H%M%S')}.json",
    )

    try:
        save_execution_output_json(
            strategy_results, history_file_path, stage_overrides=stage_overrides
        )
        save_execution_output_json(
            strategy_results,
            SCHEDULED_LATEST_RESULT_PATH,
            stage_overrides=stage_overrides,
        )
        LOGGER.info(
            "💾 Scheduled execution results saved to %s and %s",
            SCHEDULED_LATEST_RESULT_PATH,
            history_file_path,
        )
    except Exception as e:
        LOGGER.warning("⚠️ Failed to save scheduled execution results: %s", e)


def print_asset_allocation(
    asset_allocation: Dict[str, float],
    etf_descriptions: Optional[Dict[str, str]],
    total_number_of_strategy: int,
    strategy_name: str,
) -> None:
    """
    Print asset allocation results with enhanced Telegram formatting
    :param asset_allocation: Dictionary with asset allocation
    :param etf_descriptions: Dictionary mapping tickers to descriptions
    :param total_number_of_strategy: Total number of strategies
    :param strategy_name: Name of the strategy
    :return: None
    """

    # 메시지 헤더 구성 (간단한 포맷)
    strategy_display_name = strategy_name.replace("[", "").replace("]", "")
    header = f"{strategy_display_name} Strategy\n"

    # 자산 배분 정보 구성
    allocations = []
    total_allocation = 0

    for key, value in asset_allocation.items():
        percentage = round(value / total_number_of_strategy, 2)
        total_allocation += percentage

        # 자산별 이모지 매핑
        asset_emojis = {
            "SPY": "🇺🇸",
            "IWM": "🇺🇸",
            "IEFA": "🌍",
            "IEMG": "🌏",
            "TLT": "📊",
            "IEF": "📊",
            "PDBC": "🛢️",
            "VNQ": "🏢",
            "AGG": "📈",
            "LQD": "💼",
            "SHY": "💰",
            "CASH": "💵",
            "TIGER S&P500": "🐅",
            "KOSEF 200TR": "🇰🇷",
            "KODEX 골드선물(H)": "🥇",
            "TIGER 미국채 10년 선물": "📊",
            "KOSEF 국고채 10년": "🏛️",
            "QQQ": "🚀",
            "GLD": "🥇",
        }

        asset_emoji = asset_emojis.get(key, "📈")
        display_name = (
            etf_descriptions.get(key, key) if etf_descriptions else key
        )

        # 단순한 포맷 - 진행률 바 제거
        allocation_text = (
            f"{asset_emoji} {display_name}: {percentage:>6.2f}%\n"
        )
        allocations.append(allocation_text)

    # 텔레그램 줄바꿈 문제 해결: 모든 요소를 개별 메시지로 전송
    print_info_message(header.strip())

    for allocation in allocations:
        clean_allocation = allocation.strip()
        if clean_allocation:
            print_info_message(clean_allocation)


if __name__ == "__main__":
    main()
