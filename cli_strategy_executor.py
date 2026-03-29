#!/usr/bin/python3
"""Strategy execution helpers for the CLI manual analysis path."""

from typing import Dict, Optional

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
from utils.strategy_optimizer import get_required_tickers_for_strategy


def run_haa_strategy() -> Optional[Dict[str, float]]:
    """HAA 전략을 최적화된 데이터로 실행합니다."""
    try:
        required_tickers = get_required_tickers_for_strategy("haa")
        print(f"🔍 HAA 전략: {len(required_tickers)}개 자산 데이터 요청")

        data_service = DataService()
        (
            _,
            momentum_score_simple,
            _,
            _,
            _,
            _,
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
        required_tickers = get_required_tickers_for_strategy("baa")
        print(f"🔍 BAA 전략: {len(required_tickers)}개 자산 데이터 요청")

        data_service = DataService()
        momentum_score, _, _, _, sma_12month, today_price = (
            data_service.get_financial_data(" ".join(required_tickers))
        )

        return get_baa_allocation(momentum_score, sma_12month, today_price)
    except Exception as e:
        print(f"BAA strategy failed: {e}")
        return None


def run_vaa_strategy() -> Optional[Dict[str, float]]:
    """VAA 전략을 최적화된 데이터로 실행합니다."""
    try:
        required_tickers = get_required_tickers_for_strategy("vaa")
        print(f"🔍 VAA 전략: {len(required_tickers)}개 자산 데이터 요청")

        data_service = DataService()
        momentum_score, _, _, _, _, _ = data_service.get_financial_data(
            " ".join(required_tickers)
        )

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
        required_tickers = get_required_tickers_for_strategy("bdaa")
        print(f"🔍 BDAA 전략: {len(required_tickers)}개 자산 데이터 요청")

        data_service = DataService()
        _, _, _, profit_6month, _, _ = data_service.get_financial_data(
            " ".join(required_tickers)
        )

        return get_bdaa_allocation(profit_6month)
    except Exception as e:
        print(f"BDAA strategy failed: {e}")
        return None


def run_mdm_strategy() -> Optional[Dict[str, float]]:
    """MDM 전략을 최적화된 데이터로 실행합니다."""
    try:
        required_tickers = get_required_tickers_for_strategy("mdm")
        print(f"🔍 MDM 전략: {len(required_tickers)}개 자산 데이터 요청")

        data_service = DataService()
        _, _, profit_12month, profit_6month, _, _ = (
            data_service.get_financial_data(" ".join(required_tickers))
        )

        return get_mdm_allocation(profit_12month, profit_6month)
    except Exception as e:
        print(f"MDM strategy failed: {e}")
        return None
