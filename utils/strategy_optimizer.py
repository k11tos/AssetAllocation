"""
전략별 최적화된 데이터 요청 시스템

각 전략별로 필요한 ETF 티커만 추출하여 불필요한 API 호출을 방지합니다.
"""

from typing import Dict, List

from config import (
    BAA_CONFIG,
    BDAA_CONFIG,
    HAA_CONFIG,
    LAA_CONFIG,
    MDM_CONFIG,
    SECTOR_MOMENTUM_CONFIG,
    VAA_CONFIG,
)


def get_required_tickers_for_strategy(strategy_name: str) -> List[str]:
    """
    전략별로 필요한 ETF 티커 목록을 반환합니다.

    Args:
        strategy_name: 전략 이름 (haa, baa, vaa, laa, bdaa, mdm, sector_momentum)

    Returns:
        List[str]: 해당 전략에 필요한 ETF 티커 목록
    """
    strategy_tickers = {
        "haa": _get_haa_tickers(),
        "baa": _get_baa_tickers(),
        "vaa": _get_vaa_tickers(),
        "laa": _get_laa_tickers(),
        "bdaa": _get_bdaa_tickers(),
        "mdm": _get_mdm_tickers(),
        "sector_momentum": _get_sector_momentum_tickers(),
    }

    return strategy_tickers.get(strategy_name.lower(), [])


def _get_haa_tickers() -> List[str]:
    """HAA 전략에 필요한 티커 목록"""
    # HAA는 OFFENSIVE + DEFENSIVE + CANARY 유니버스 사용
    tickers = (
        HAA_CONFIG.OFFENSIVE_TICKERS
        + HAA_CONFIG.DEFENSIVE_TICKERS
        + HAA_CONFIG.CANARY_TICKERS
    )
    return list(dict.fromkeys(tickers))


def _get_baa_tickers() -> List[str]:
    """BAA 전략에 필요한 티커 목록"""
    # BAA는 공격자 자산 + 방어자 자산
    return BAA_CONFIG.ATTACKER_TICKERS + BAA_CONFIG.DEFENDER_TICKERS


def _get_vaa_tickers() -> List[str]:
    """VAA 전략에 필요한 티커 목록"""
    # VAA는 공격자 자산 + 방어자 자산
    return VAA_CONFIG.ATTACKER_TICKERS + VAA_CONFIG.DEFENDER_TICKERS


def _get_laa_tickers() -> List[str]:
    """LAA 전략에 필요한 티커 목록"""
    # LAA는 BASE_ALLOCATION의 키들 + QQQ (동적 할당용)
    base_tickers = list(LAA_CONFIG.BASE_ALLOCATION.keys())
    return base_tickers + ["QQQ"]


def _get_bdaa_tickers() -> List[str]:
    """BDAA 전략에 필요한 티커 목록"""
    # BDAA는 채권 자산만 필요
    return BDAA_CONFIG.BOND_TICKERS


def _get_mdm_tickers() -> List[str]:
    """MDM 전략에 필요한 티커 목록"""
    # MDM은 주식 자산 + 채권 자산
    return ["SPY", "IEFA"] + MDM_CONFIG.BOND_TICKERS


def _get_sector_momentum_tickers() -> List[str]:
    """Sector Momentum 전략에 필요한 티커 목록"""
    tickers = (
        SECTOR_MOMENTUM_CONFIG.SECTOR_TICKERS
        + [SECTOR_MOMENTUM_CONFIG.DEFENSIVE_TICKER]
    )
    return list(dict.fromkeys(tickers))


def get_all_required_tickers(strategies: List[str]) -> List[str]:
    """
    여러 전략에 필요한 모든 티커를 중복 제거하여 반환합니다.

    Args:
        strategies: 전략 이름 목록

    Returns:
        List[str]: 중복이 제거된 모든 필요한 티커 목록
    """
    all_tickers = set()

    for strategy in strategies:
        strategy_tickers = get_required_tickers_for_strategy(strategy)
        all_tickers.update(strategy_tickers)

    return sorted(list(all_tickers))


def get_strategy_optimization_info() -> Dict[str, Dict[str, object]]:
    """
    전략별 최적화 정보를 반환합니다.

    Returns:
        Dict[str, Dict[str, object]]: 전략별 티커 수와 최적화 정보
    """
    info = {}

    for strategy in ["haa", "baa", "vaa", "laa", "bdaa", "mdm", "sector_momentum"]:
        required_tickers = get_required_tickers_for_strategy(strategy)
        info[strategy.upper()] = {
            "required_tickers": len(required_tickers),
            "tickers": required_tickers,
        }

    return info


def print_optimization_summary() -> None:
    """최적화 요약 정보를 출력합니다."""
    print("📊 전략별 최적화 요약")
    print("=" * 50)

    info = get_strategy_optimization_info()
    total_current = 22  # 현재 us_etf_tickers.json의 총 개수

    for strategy, data in info.items():
        required = data["required_tickers"]
        savings = total_current - required
        savings_pct = (savings / total_current) * 100

        print(
            f"{strategy:>4}: {required:>2}개 티커 필요 "
            f"(절약: {savings}개, {savings_pct:.1f}%)"
        )

    print("=" * 50)
    print(f"현재 전체: {total_current}개 티커")
    print("최적화 후: 전략별 4-10개 티커 (50-80% 절약)")
