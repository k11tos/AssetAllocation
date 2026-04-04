#!/usr/bin/python3
"""
Command Line Interface for Asset Allocation
"""

import argparse
import json
import os
import sys
from numbers import Real
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import STRATEGY_CONFIG
from strategies.haa_strategy import HAAStrategy
from execution_output import (
    build_execution_output_data,
    format_compact_execution_diff_summary,
    format_execution_diff_summary,
    load_execution_output_json as _load_execution_output_json,
    save_execution_output_json,
)
from main import main as run_main
from portfolio import (
    calculate_rebalancing,
)
from utils.performance_monitor import get_performance_monitor
from strategy_runner import run_selected_strategies
from utils.strategy_optimizer import (
    get_required_tickers_for_strategy,
    print_optimization_summary,
)
from services.data_service import DataService

DEFAULT_HISTORY_DIR = "outputs/history"
_format_compact_execution_diff_summary = format_compact_execution_diff_summary


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

    parser.add_argument(
        "--save-json",
        type=str,
        help="전략 실행 결과를 JSON 파일로 저장할 경로 (예: outputs/latest.json)",
    )

    parser.add_argument(
        "--compare-json",
        type=str,
        help=(
            "현재 전략 실행 결과를 이전 JSON 결과와 비교할 경로 "
            "(예: outputs/previous.json)"
        ),
    )

    parser.add_argument(
        "--history",
        nargs="?",
        const=10,
        type=int,
        help=(
            "저장된 실행 기록 요약 조회 "
            "(기본 최근 10개, 예: --history 5)"
        ),
    )

    parser.add_argument(
        "--show-history",
        type=str,
        help="저장된 실행 스냅샷 JSON 파일 상세 조회 (예: outputs/history/20260101_000000.json)",
    )

    # 리밸런싱
    parser.add_argument(
        "--rebalance",
        type=str,
        help="리밸런싱 정보가 담긴 JSON 파일 경로",
    )
    parser.add_argument(
        "--haa-debug-report",
        action="store_true",
        help=(
            "HAA 한 번 실행의 의사결정 디버그 리포트 출력 "
            "(전략 검증용, --strategy haa와 함께 권장)"
        ),
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
    output_data = build_execution_output_data(results)
    return json.dumps(output_data, indent=2, ensure_ascii=False)


def load_execution_output_json(file_path: str) -> Dict[str, Any]:
    """저장된 전략 실행 결과 JSON 파일을 로드합니다."""
    try:
        return _load_execution_output_json(file_path)
    except FileNotFoundError:
        print(f"Error: Compare file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in compare file: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


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


def _get_recent_history_file_paths(
    history_dir: str, limit: int
) -> List[str]:
    """히스토리 디렉토리에서 최신 스냅샷 파일 경로를 반환합니다."""
    if limit <= 0:
        raise ValueError("History count must be greater than 0")
    if not os.path.isdir(history_dir):
        return []

    history_file_names = [
        file_name
        for file_name in os.listdir(history_dir)
        if file_name.endswith(".json")
    ]
    history_file_names.sort(reverse=True)
    return [
        os.path.join(history_dir, file_name)
        for file_name in history_file_names[:limit]
    ]


def format_history_summary(history_dir: str, limit: int) -> str:
    """저장된 실행 히스토리 스냅샷을 간결하게 요약합니다."""
    history_file_paths = _get_recent_history_file_paths(history_dir, limit)
    if not history_file_paths:
        return (
            f"No history snapshots found in {history_dir}. "
            "Run scheduled/main execution first."
        )

    output = [
        f"Execution History (latest {len(history_file_paths)})",
        "=" * 60,
    ]

    for index, file_path in enumerate(history_file_paths, start=1):
        file_name = os.path.basename(file_path)
        try:
            data = _load_execution_output_json(file_path)
            timestamp = data.get("timestamp", "unknown")
            strategies = data.get("strategies", {})
            strategy_names = (
                sorted(strategies.keys()) if isinstance(strategies, dict) else []
            )
            strategy_count = len(strategy_names)
            strategy_display = ", ".join(strategy_names) if strategy_names else "-"
            output.append(
                f"{index:>2}. {timestamp} | file={file_name} | "
                f"strategies={strategy_count} [{strategy_display}]"
            )
        except Exception as e:
            output.append(
                f"{index:>2}. {file_name} | status=invalid snapshot ({e})"
            )

    return "\n".join(output)


def format_history_snapshot_detail(
    snapshot_data: Dict[str, Any], snapshot_path: Optional[str] = None
) -> str:
    """저장된 실행 스냅샷 한 건의 상세 정보를 사람이 읽기 쉬운 형식으로 포맷합니다."""
    timestamp = snapshot_data.get("timestamp", "unknown")
    strategies = snapshot_data.get("strategies", {})
    strategy_names = sorted(strategies.keys()) if isinstance(strategies, dict) else []

    output = ["Execution Snapshot Detail", "=" * 60]
    if snapshot_path:
        output.append(f"File: {snapshot_path}")
    output.append(f"Timestamp: {timestamp}")
    output.append(f"Strategy count: {len(strategy_names)}")
    output.append(
        f"Strategies: {', '.join(strategy_names) if strategy_names else 'none'}"
    )

    if not strategy_names:
        return "\n".join(output)

    output.append("")
    for strategy_name in strategy_names:
        allocation = strategies.get(strategy_name)
        output.append(f"[{strategy_name}]")
        if isinstance(allocation, dict):
            output.append(f"  Assets: {len(allocation)}")
            if allocation:
                for asset, percentage in sorted(allocation.items()):
                    if isinstance(percentage, Real) and not isinstance(
                        percentage, bool
                    ):
                        output.append(f"  - {asset}: {percentage:.2f}%")
                    else:
                        output.append(f"  - {asset}: invalid value ({percentage})")
            else:
                output.append("  - no allocations")
        else:
            output.append("  Assets: n/a")
            output.append(f"  - result: {allocation}")

    return "\n".join(output)


def main():
    """CLI 메인 함수"""
    parser = create_parser()
    args = parser.parse_args()

    # 로그 레벨 설정
    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

    if args.show_history:
        try:
            snapshot_data = _load_execution_output_json(args.show_history)
        except FileNotFoundError:
            print(f"Error: Snapshot file not found: {args.show_history}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in snapshot file: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        if args.output == "json":
            print(json.dumps(snapshot_data, indent=2, ensure_ascii=False))
        else:
            print(format_history_snapshot_detail(snapshot_data, args.show_history))
        return

    if args.history is not None:
        if args.history <= 0:
            print("Error: --history count must be greater than 0")
            sys.exit(1)
        print(format_history_summary(DEFAULT_HISTORY_DIR, args.history))
        return

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
    if args.haa_debug_report:
        if args.strategy != "haa":
            print("Error: --haa-debug-report requires --strategy haa")
            sys.exit(1)

        required_tickers = get_required_tickers_for_strategy("haa")
        data_service = DataService()
        (_, momentum_score_simple, _, _, _, _) = data_service.get_financial_data(
            " ".join(required_tickers)
        )
        evaluation_date = data_service.get_last_market_data_date() or "unknown"
        report = HAAStrategy().build_debug_report(
            momentum_score_simple=momentum_score_simple,
            evaluation_date=evaluation_date,
        )
        print(report)
        return

    available_strategies = ["HAA", "KAW", "BAA", "VAA", "LAA", "BDAA", "MDM"]
    if args.strategy == "all":
        requested_strategies = available_strategies
    else:
        requested_strategies = [args.strategy.upper()]

    results = run_selected_strategies(requested_strategies, "cli")

    if args.save_json:
        save_execution_output_json(results, args.save_json)

    diff_output = None
    if args.compare_json:
        previous_data = load_execution_output_json(args.compare_json)
        diff_output = format_execution_diff_summary(previous_data, results)

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

    if diff_output and args.output == "text":
        print()
        print(diff_output)

    # 성능 모니터링 결과 출력
    if args.performance:
        performance_monitor = get_performance_monitor()
        performance_monitor.log_summary()


if __name__ == "__main__":
    main()
