#!/usr/bin/python3
"""
Command Line Interface for Asset Allocation
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from main import main as run_main
from portfolio import (
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

    return parser


def load_tickers(file_path: str) -> list:
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


def main():
    """CLI 메인 함수"""
    parser = create_parser()
    args = parser.parse_args()

    # 로그 레벨 설정
    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

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
    results = {}

    if args.strategy in ["haa", "all"]:
        results["HAA"] = run_haa_strategy()

    if args.strategy in ["kaw", "all"]:
        results["KAW"] = run_kaw_strategy()

    if args.strategy in ["baa", "all"]:
        results["BAA"] = run_baa_strategy()

    if args.strategy in ["vaa", "all"]:
        results["VAA"] = run_vaa_strategy()

    if args.strategy in ["laa", "all"]:
        results["LAA"] = run_laa_strategy()

    if args.strategy in ["bdaa", "all"]:
        results["BDAA"] = run_bdaa_strategy()

    if args.strategy in ["mdm", "all"]:
        results["MDM"] = run_mdm_strategy()

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
