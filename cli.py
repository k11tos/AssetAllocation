#!/usr/bin/python3
"""
Command Line Interface for Asset Allocation
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import STRATEGY_CONFIG
from main import main as run_main
from portfolio import (
    calculate_rebalancing,
    get_baa_allocation,
    get_bdaa_allocation,
    get_hybrid_asset_allocation,
    get_korean_all_weather_allocation,
    get_laa_allocation,
    get_mdm_allocation,
    get_vaa_allocation,
)
from services.data_service import DataService
from utils.cache_manager import CacheManager
from utils.performance_monitor import get_performance_monitor
from strategy_runner import run_selected_strategies
from utils.strategy_optimizer import (
    get_required_tickers_for_strategy,
    print_optimization_summary,
)


def create_parser() -> argparse.ArgumentParser:
    """CLI 파서를 생성합니다."""
    parser = argparse.ArgumentParser(
        description="Asset Allocation Strategy Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py                    # 기본 실행 (HAA + KAW 전략)
  python cli.py --strategy haa     # HAA 전략만 실행
  python cli.py --strategy kaw     # KAW 전략만 실행
  python cli.py --output json      # JSON 형식으로 출력
  python cli.py --output csv       # CSV 형식으로 출력
  python cli.py --verbose          # 상세 로그 출력
  python cli.py --cache-stats      # 캐시 통계 출력
        """,
    )

    # 전략 선택
    parser.add_argument(
        "--strategy",
        choices=["haa", "kaw", "baa", "vaa", "laa", "bdaa", "mdm", "all"],
        default="all",
        help="실행할 전략 선택 (기본값: all)",
    )

    # 출력 형식
    parser.add_argument(
        "--output",
        choices=["text", "json", "csv"],
        default="text",
        help="출력 형식 선택 (기본값: text)",
    )

    # 로그 레벨
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="상세 로그 출력"
    )

    # 캐시 관리
    parser.add_argument("--cache-stats", action="store_true", help="캐시 통계 출력")

    parser.add_argument("--clear-cache", action="store_true", help="캐시 정리")

    # 티커 파일
    parser.add_argument(
        "--tickers", type=str, help="사용할 티커 파일 경로 (기본값: us_etf_tickers.json)"
    )

    # 성능 모니터링
    parser.add_argument(
        "--performance", action="store_true", help="성능 모니터링 결과 출력"
    )

    # 리밸런싱
    parser.add_argument(
        "--rebalance",
        type=str,
        help="리밸런싱 정보가 담긴 JSON 파일 경로",
    )

    return parser


def load_tickers(file_path: str) -> List[str]:
    """티커 목록을 로드합니다."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Ticker file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in ticker file: {e}")
        sys.exit(1)


def format_output_text(results: Dict[str, Any]) -> str:
    """텍스트 형식으로 출력을 포맷합니다."""
    output = []
    output.append(
        f"Asset Allocation Report - "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    output.append("=" * 60)

    for strategy_name, allocation in results.items():
        if allocation is None:
            output.append(f"\n{strategy_name}: Failed to execute")
            continue

        output.append(f"\n{strategy_name}:")
        output.append("-" * 40)

        for asset, percentage in allocation.items():
            output.append(f"  {asset}: {percentage:.2f}%")

    return "\n".join(output)


def format_output_json(results: Dict[str, Any]) -> str:
    """JSON 형식으로 출력을 포맷합니다."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "strategies": results,
    }
    return json.dumps(output_data, indent=2, ensure_ascii=False)


def format_output_csv(results: Dict[str, Any]) -> str:
    """CSV 형식으로 출력을 포맷합니다."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # 헤더
    writer.writerow(["Strategy", "Asset", "Percentage"])

    # 데이터
    for strategy_name, allocation in results.items():
        if allocation is None:
            writer.writerow([strategy_name, "ERROR", "0.00"])
            continue

        for asset, percentage in allocation.items():
            writer.writerow([strategy_name, asset, f"{percentage:.2f}"])

    return output.getvalue()


def load_rebalance_data(file_path: str) -> Dict[str, Any]:
    """리밸런싱 데이터를 로드합니다."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"Error: Rebalance file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in rebalance file: {e}")
        sys.exit(1)


def format_rebalance_text(rebalance_results: Dict[str, Any]) -> str:
    """리밸런싱 결과를 텍스트 형식으로 포맷합니다."""
    output = []
    output.append(f"리밸런싱 리포트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 80)

    for ticker, info in rebalance_results.items():
        output.append(f"\n{ticker}:")
        output.append(f"  현재가: ${info['price']:.2f}")
        output.append(f"  현재 수량: {info['current_quantity']}")
        output.append(f"  현재 가치: ${info['current_value']:.2f}")
        output.append(f"  현재 비중: {info['current_allocation_pct']:.2f}%")
        output.append(f"  목표 비중: {info['target_allocation_pct']:.2f}%")
        output.append(f"  목표 가치: ${info['target_value']:.2f}")
        output.append(f"  목표 수량: {info['target_quantity']}")
        output.append(f"  조치: {info['action']} ({info['quantity_diff']:+d} 주)")

    return "\n".join(output)


def format_rebalance_json(rebalance_results: Dict[str, Any]) -> str:
    """리밸런싱 결과를 JSON 형식으로 포맷합니다."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "rebalancing": rebalance_results,
    }
    return json.dumps(output_data, indent=2, ensure_ascii=False)


def format_rebalance_csv(rebalance_results: Dict[str, Any]) -> str:
    """리밸런싱 결과를 CSV 형식으로 포맷합니다."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # 헤더
    writer.writerow(
        [
            "Ticker",
            "현재가",
            "현재 수량",
            "현재 가치",
            "현재 비중 (%)",
            "목표 비중 (%)",
            "목표 가치",
            "목표 수량",
            "차이",
            "조치",
        ]
    )

    # 데이터
    for ticker, info in rebalance_results.items():
        writer.writerow(
            [
                ticker,
                f"{info['price']:.2f}",
                info["current_quantity"],
                f"{info['current_value']:.2f}",
                f"{info['current_allocation_pct']:.2f}",
                f"{info['target_allocation_pct']:.2f}",
                f"{info['target_value']:.2f}",
                info["target_quantity"],
                info["quantity_diff"],
                info["action"],
            ]
        )

    return output.getvalue()


def run_haa_strategy() -> Optional[Dict[str, float]]:
    """HAA 전략을 최적화된 데이터로 실행합니다."""
    try:
        # HAA 전략에 필요한 티커만 추출
        required_tickers = get_required_tickers_for_strategy("haa")
        print(f"🔍 HAA 전략: {len(required_tickers)}개 자산 데이터 요청")

        data_service = DataService()
        (
            momentum_score,
            momentum_score_simple,
            profit_12month,
            profit_6month,
            sma_12month,
            today_price,
        ) = data_service.get_financial_data(" ".join(required_tickers))

        return get_hybrid_asset_allocation(momentum_score_simple)
    except Exception as e:
        print(f"HAA strategy failed: {e}")
        return None


def run_kaw_strategy() -> Optional[Dict[str, float]]:
    """한국형 올웨더 전략을 실행합니다."""
    try:
        return get_korean_all_weather_allocation()
    except Exception as e:
        print(f"KAW strategy failed: {e}")
        return None


def run_baa_strategy() -> Optional[Dict[str, float]]:
    """BAA 전략을 최적화된 데이터로 실행합니다."""
    try:
        # BAA 전략에 필요한 티커만 추출
        required_tickers = get_required_tickers_for_strategy("baa")
        print(f"🔍 BAA 전략: {len(required_tickers)}개 자산 데이터 요청")

        data_service = DataService()
        (
            momentum_score,
            momentum_score_simple,
            profit_12month,
            profit_6month,
            sma_12month,
            today_price,
        ) = data_service.get_financial_data(" ".join(required_tickers))

        return get_baa_allocation(momentum_score, sma_12month, today_price)
    except Exception as e:
        print(f"BAA strategy failed: {e}")
        return None


def run_vaa_strategy() -> Optional[Dict[str, float]]:
    """VAA 전략을 최적화된 데이터로 실행합니다."""
    try:
        # VAA 전략에 필요한 티커만 추출
        required_tickers = get_required_tickers_for_strategy("vaa")
        print(f"🔍 VAA 전략: {len(required_tickers)}개 자산 데이터 요청")

        data_service = DataService()
        (
            momentum_score,
            momentum_score_simple,
            profit_12month,
            profit_6month,
            sma_12month,
            today_price,
        ) = data_service.get_financial_data(" ".join(required_tickers))

        return get_vaa_allocation(momentum_score)
    except Exception as e:
        print(f"VAA strategy failed: {e}")
        return None


def run_laa_strategy() -> Optional[Dict[str, float]]:
    """LAA 전략을 실행합니다."""
    try:
        data_service = DataService()
        sp500 = data_service.get_fred_data("SP500")
        unrate = data_service.get_fred_data("UNRATE")
        return get_laa_allocation(sp500, unrate)
    except Exception as e:
        print(f"LAA strategy failed: {e}")
        return None


def run_bdaa_strategy() -> Optional[Dict[str, float]]:
    """BDAA 전략을 최적화된 데이터로 실행합니다."""
    try:
        # BDAA 전략에 필요한 티커만 추출
        required_tickers = get_required_tickers_for_strategy("bdaa")
        print(f"🔍 BDAA 전략: {len(required_tickers)}개 자산 데이터 요청")

        data_service = DataService()
        (
            momentum_score,
            momentum_score_simple,
            profit_12month,
            profit_6month,
            sma_12month,
            today_price,
        ) = data_service.get_financial_data(" ".join(required_tickers))

        return get_bdaa_allocation(profit_6month)
    except Exception as e:
        print(f"BDAA strategy failed: {e}")
        return None


def run_mdm_strategy() -> Optional[Dict[str, float]]:
    """MDM 전략을 최적화된 데이터로 실행합니다."""
    try:
        # MDM 전략에 필요한 티커만 추출
        required_tickers = get_required_tickers_for_strategy("mdm")
        print(f"🔍 MDM 전략: {len(required_tickers)}개 자산 데이터 요청")

        data_service = DataService()
        (
            momentum_score,
            momentum_score_simple,
            profit_12month,
            profit_6month,
            sma_12month,
            today_price,
        ) = data_service.get_financial_data(" ".join(required_tickers))

        return get_mdm_allocation(profit_12month, profit_6month)
    except Exception as e:
        print(f"MDM strategy failed: {e}")
        return None




def get_available_strategy_runners():
    """실행 가능한 전략 러너 매핑을 반환합니다."""
    return {
        "HAA": run_haa_strategy,
        "KAW": run_kaw_strategy,
        "BAA": run_baa_strategy,
        "VAA": run_vaa_strategy,
        "LAA": run_laa_strategy,
        "BDAA": run_bdaa_strategy,
        "MDM": run_mdm_strategy,
    }


def main():
    """CLI 메인 함수"""
    parser = create_parser()
    args = parser.parse_args()

    # 로그 레벨 설정
    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

    # 티커 파일 설정
    if args.tickers:
        # 티커 파일 유효성 검증 및 로드
        load_tickers(args.tickers)
        # 설정 업데이트
        STRATEGY_CONFIG.TICKER_FILE = args.tickers

    # 리밸런싱 모드
    if args.rebalance:
        rebalance_data = load_rebalance_data(args.rebalance)

        # 필수 필드 검증
        required_fields = ["allocation", "current_prices", "current_balances"]
        for field in required_fields:
            if field not in rebalance_data:
                print(
                    f"Error: Missing required field '{field}' "
                    f"in rebalance file"
                )
                sys.exit(1)

        allocation = rebalance_data["allocation"]
        current_prices = rebalance_data["current_prices"]
        current_balances = rebalance_data["current_balances"]

        # 리밸런싱 계산
        rebalance_results = calculate_rebalancing(
            allocation, current_prices, current_balances
        )

        # 출력 형식에 따라 결과 출력
        if args.output == "json":
            print(format_rebalance_json(rebalance_results))
        elif args.output == "csv":
            print(format_rebalance_csv(rebalance_results))
        else:  # text
            print(format_rebalance_text(rebalance_results))

        return

    # 캐시 관리
    if args.cache_stats or args.clear_cache:
        data_service = DataService()

        if args.cache_stats:
            stats = data_service.get_cache_stats()
            print("Cache Statistics:")
            print(f"  Total files: {stats['total_files']}")
            print(f"  Total size: {stats['total_size_mb']} MB")
            print(f"  Cache directory: {stats['cache_dir']}")
            print(f"  TTL: {stats['ttl_hours']} hours")

        if args.clear_cache:
            cleared = data_service.clear_cache()
            print(f"Cleared {cleared} cache files")

        return

    # 전략 실행
    strategy_runners = get_available_strategy_runners()
    if args.strategy == "all":
        requested_strategies = list(strategy_runners.keys())
    else:
        requested_strategies = [args.strategy.upper()]

    results = run_selected_strategies(requested_strategies, strategy_runners)

    # 최적화 요약 출력 (verbose 모드에서만)
    if args.verbose:
        print("\n" + "=" * 60)
        print_optimization_summary()
        print("=" * 60 + "\n")

    # 출력 형식에 따라 결과 출력
    if args.output == "json":
        print(format_output_json(results))
    elif args.output == "csv":
        print(format_output_csv(results))
    else:  # text
        print(format_output_text(results))

    # 성능 모니터링 결과 출력
    if args.performance:
        performance_monitor = get_performance_monitor()
        performance_monitor.log_summary()


if __name__ == "__main__":
    main()
