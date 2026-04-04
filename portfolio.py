#!/usr/bin/python3
"""
Portfolio management module - refactored for better structure
"""

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# Load environment variables
from dotenv import load_dotenv

from config import BDAA_CONFIG
from services.communication_service import CommunicationService
from services.data_service import DataService
from strategies import HAAStrategy, KoreanAllWeatherStrategy
from utils.logging_config import LoggingConfig

load_dotenv()

LOGGER = LoggingConfig.get_logger(__name__)


class AllocationConstants:
    """자산 배분 관련 상수들"""

    # 기본 배분 비율
    FULL_ALLOCATION = 100.0

    # 로깅 관련
    DECIMAL_PLACES = 3


def get_laa_allocation(sp500: Any, unrate: Any) -> Dict[str, float]:
    """
    Get allocation for LAA (Lethargic Asset Allocation) strategy
    using the LAA strategy class
    :param sp500: S&P 500 time series data from FRED
    :param unrate: Unemployment rate time series data from FRED
    :return: Dictionary with asset allocation percentages
    """
    from strategies.laa_strategy import LAAStrategy

    laa_strategy = LAAStrategy()
    data = {"sp500": sp500, "unrate": unrate}

    return laa_strategy.calculate_allocation(data)


def get_original_dual_momentum(
    profit_12month: Dict[str, float]
) -> Dict[str, float]:
    """
    Get ticker for original dual momentum
    :param profit_12month: Dictionary with 12-month profit data
    :return: Dictionary with asset allocation percentages
    """
    odm = {}

    LOGGER.debug(
        f"📊 SPY 12 months average: "
        f"{round(profit_12month['SPY'], AllocationConstants.DECIMAL_PLACES)}"
    )
    LOGGER.debug(
        f"📊 BIL 12 months average: "
        f"{round(profit_12month['BIL'], AllocationConstants.DECIMAL_PLACES)}"
    )
    LOGGER.debug(
        f"📊 IEFA 12 months average: "
        f"{round(profit_12month['IEFA'], AllocationConstants.DECIMAL_PLACES)}"
    )

    if profit_12month["SPY"] > profit_12month["BIL"]:
        if profit_12month["SPY"] >= profit_12month["IEFA"]:
            odm["SPY"] = AllocationConstants.FULL_ALLOCATION
        else:
            odm["IEFA"] = AllocationConstants.FULL_ALLOCATION
    else:
        odm["AGG"] = AllocationConstants.FULL_ALLOCATION

    return odm


def get_vaa_allocation(momentum_score: Dict[str, float]) -> Dict[str, float]:
    """
    Get allocation for VAA (Vigilant Asset Allocation) strategy
    using the VAA strategy class
    :param momentum_score: Dictionary with momentum scores
    :return: Dictionary with asset allocation percentages
    """
    from strategies.vaa_strategy import VAAStrategy

    vaa_strategy = VAAStrategy()
    data = {"momentum_score": momentum_score}

    return vaa_strategy.calculate_allocation(data)


def get_baa_allocation(
    momentum_score: Dict[str, float],
    sma_12month: Dict[str, float],
    today_price: Dict[str, float],
) -> Dict[str, float]:
    """
    Get allocation for BAA (Bold Asset Allocation) strategy
    using the BAA strategy class
    :param momentum_score: Dictionary with momentum scores
    :param sma_12month: Dictionary with 12-month moving averages
    :param today_price: Dictionary with current prices
    :return: Dictionary with asset allocation percentages
    """
    from strategies.baa_strategy import BAAStrategy

    baa_strategy = BAAStrategy()
    data = {
        "momentum_score": momentum_score,
        "sma_12month": sma_12month,
        "today_price": today_price,
    }

    return baa_strategy.calculate_allocation(data)


def get_bdaa_allocation(profit_6month: Dict[str, float]) -> Dict[str, float]:
    """
    Get allocation for BDAA (Bond Dynamic Asset Allocation) strategy
    using the BDAA strategy class
    :param profit_6month: Dictionary with 6-month profit data
    :return: Dictionary with asset allocation percentages
    """
    from strategies.bdaa_strategy import BDAAStrategy

    bdaa_strategy = BDAAStrategy()
    data = {"profit_6month": profit_6month}

    return bdaa_strategy.calculate_allocation(data)


def get_mdm_allocation(
    profit_12month: Dict[str, float], profit_6month: Dict[str, float]
) -> Dict[str, float]:
    """
    Get allocation for MDM (Modified Dual Momentum) strategy
    using the MDM strategy class
    :param profit_12month: Dictionary with 12-month profit data
    :param profit_6month: Dictionary with 6-month profit data
    :return: Dictionary with asset allocation percentages
    """
    from strategies.mdm_strategy import MDMStrategy

    mdm_strategy = MDMStrategy()
    data = {"profit_12month": profit_12month, "profit_6month": profit_6month}

    return mdm_strategy.calculate_allocation(data)


def get_bond_dynamic_asset_allocation(
    profit_6month: Dict[str, float]
) -> Dict[str, float]:
    """
    Get ticker for BDAA (Bond Dynamic Asset Allocation)
    :param profit_6month: Dictionary with 6-month profit data
    :return: Dictionary with asset allocation percentages
    """
    bdaa = {}

    bond_profit_dict = {
        "SHY": profit_6month["SHY"],
        "IEF": profit_6month["IEF"],
        "TLT": profit_6month["TLT"],
        "TIP": profit_6month["TIP"],
        "LQD": profit_6month["LQD"],
        "HYG": profit_6month["HYG"],
        "BWX": profit_6month["BWX"],
        "EMB": profit_6month["EMB"],
    }

    bond_profit_top3 = sorted(
        bond_profit_dict.items(), key=lambda x: x[1], reverse=True
    )[: BDAA_CONFIG.TOP_BONDS_COUNT]

    cash: float = 0
    for key, value in bond_profit_top3:
        if value < 0:
            cash += BDAA_CONFIG.BOND_ALLOCATION_RATIO
        else:
            bdaa[key] = BDAA_CONFIG.BOND_ALLOCATION_RATIO

    if cash > 0:
        bdaa["CASH"] = cash

    return bdaa


def get_hybrid_asset_allocation(
    momentum_score_simple: Dict[str, float]
) -> Dict[str, float]:
    """
    HAA (Hybrid Asset Allocation) 전략을 실행합니다.

    Args:
        momentum_score_simple: 단순 모멘텀 스코어 딕셔너리

    Returns:
        자산 배분 딕셔너리
    """
    haa_strategy = HAAStrategy()
    data = {"momentum_score_simple": momentum_score_simple}
    return haa_strategy.execute(data)


def get_korean_all_weather_allocation() -> Dict[str, float]:
    """
    한국형 올웨더 전략을 실행합니다.

    Returns:
        자산 배분 딕셔너리
    """
    kaw_strategy = KoreanAllWeatherStrategy()
    data: Dict[str, Any] = {}  # 한국형 올웨더 전략은 추가 데이터가 필요하지 않음
    return kaw_strategy.execute(data)


def print_info_message(message_string: str) -> None:
    """
    정보 메시지를 출력하고 텔레그램으로 전송합니다.

    Args:
        message_string: 출력할 메시지
    """
    print_info_messages([message_string])


def print_info_messages(messages: Sequence[str]) -> None:
    """정보 메시지 목록을 출력하고 텔레그램으로 전송합니다."""
    try:
        communication_service = CommunicationService()
        success = communication_service.send_messages(messages)

        if success:
            preview = messages[0][:50] if messages else ""
            LOGGER.debug(f"📤 Messages sent via Telegram: {preview}...")
        else:
            LOGGER.info("📤 Telegram send failed, logged locally: %s", messages)

    except Exception as e:
        LoggingConfig.log_error_with_context(
            LOGGER,
            e,
            "print_info_messages",
            {"message_count": len(messages)},
        )
        LOGGER.info("📤 Messages logged locally: %s", messages)


# Service factory functions
def get_data_service() -> DataService:
    """데이터 서비스 인스턴스를 반환합니다."""
    return DataService()


def get_communication_service() -> CommunicationService:
    """통신 서비스 인스턴스를 반환합니다."""
    return CommunicationService()


def get_financial_data(
    tickers: str,
) -> Tuple[
    Dict[str, float],
    Dict[str, float],
    Dict[str, float],
    Dict[str, float],
    Dict[str, float],
    Dict[str, float],
]:
    """
    주어진 티커들의 금융 데이터를 가져옵니다.

    Args:
        tickers: 공백으로 구분된 티커 심볼 문자열

    Returns:
        (momentum_score, momentum_score_simple, profit_12month,
         profit_6month, sma_12month, today_price) 튜플
    """
    data_service = get_data_service()
    return data_service.get_financial_data(tickers)


def calculate_rebalancing(
    allocation: Dict[str, float],
    current_prices: Dict[str, float],
    current_balances: Dict[str, int],
    total_portfolio_value: Optional[float] = None,
) -> Dict[str, Dict[str, Union[float, int]]]:
    """
    현재가와 잔고를 입력받아 리밸런싱 수량을 계산합니다.

    Args:
        allocation: 자산 배분 딕셔너리 (티커: 비율 %)
        current_prices: 현재가 딕셔너리 (티커: 가격)
        current_balances: 현재 잔고 딕셔너리 (티커: 수량)
        total_portfolio_value: 총 포트폴리오 가치 (선택, 자동 계산 가능)

    Returns:
        각 자산별 리밸런싱 정보 (현재 가치, 목표 가치, 매수/매도 수량 등)
    """
    # 1. 총 포트폴리오 가치 계산
    if total_portfolio_value is None:
        total_portfolio_value = sum(
            current_prices.get(ticker, 0) * qty
            for ticker, qty in current_balances.items()
        )

    rebalance_info = {}

    all_tickers = set(allocation.keys()) | set(current_balances.keys())

    for ticker in all_tickers:
        target_pct = allocation.get(ticker, 0.0)
        price = current_prices.get(ticker, 0)
        current_qty = current_balances.get(ticker, 0)

        # Skip if we have no balance and no allocation
        # (shouldn't happen with the set logic, but good for safety)
        if current_qty == 0 and target_pct == 0:
            continue

        # 현재 가치와 목표 가치 계산
        current_value = price * current_qty
        target_value = total_portfolio_value * (target_pct / 100)

        # 목표 수량 계산 (정수로 반올림)
        if price > 0:
            target_qty = int(target_value / price)
        else:
            target_qty = 0

        # 매수/매도 수량 차이
        qty_diff = target_qty - current_qty

        # 액션 결정
        if price <= 0 and target_pct > 0:
            action = "가격 정보 없음"
        elif qty_diff > 0:
            action = "매수"
        elif qty_diff < 0:
            action = "매도"
        else:
            action = "유지"

        rebalance_info[ticker] = {
            "current_value": round(current_value, 2),
            "target_value": round(target_value, 2),
            "current_quantity": current_qty,
            "target_quantity": target_qty,
            "quantity_diff": qty_diff,
            "action": action,
            "price": round(price, 2),
            "target_allocation_pct": target_pct,
            "current_allocation_pct": round(
                (current_value / total_portfolio_value * 100), 2
            )
            if total_portfolio_value > 0
            else 0,
        }

    return rebalance_info
