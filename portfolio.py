#!/usr/bin/python3
"""
Portfolio management module - refactored for better structure
"""

import logging
from typing import Dict, Tuple

# Load environment variables
from dotenv import load_dotenv

from config import BDAA_CONFIG
from services.communication_service import CommunicationService
from services.data_service import DataService
from strategies import HAAStrategy, KoreanAllWeatherStrategy

load_dotenv()

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


class AllocationConstants:
    """자산 배분 관련 상수들"""

    # 기본 배분 비율
    FULL_ALLOCATION = 100.0

    # 로깅 관련
    DECIMAL_PLACES = 3


def get_laa_allocation(sp500, unrate) -> Dict[str, float]:
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
        "SPY 12 months average: %s",
        round(profit_12month["SPY"], AllocationConstants.DECIMAL_PLACES),
    )
    LOGGER.debug(
        "BIL 12 months average: %s",
        round(profit_12month["BIL"], AllocationConstants.DECIMAL_PLACES),
    )
    LOGGER.debug(
        "IEFA 12 months average: %s",
        round(profit_12month["IEFA"], AllocationConstants.DECIMAL_PLACES),
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

    cash = 0
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
    data = {}  # 한국형 올웨더 전략은 추가 데이터가 필요하지 않음
    return kaw_strategy.execute(data)


def print_info_message(message_string: str) -> None:
    """
    정보 메시지를 출력하고 텔레그램으로 전송합니다.

    Args:
        message_string: 출력할 메시지
    """
    try:
        communication_service = CommunicationService()
        success = communication_service.send_message(message_string)

        if success:
            LOGGER.debug(
                f"Message sent via Telegram: {message_string[:50]}..."
            )
        else:
            LOGGER.info(
                f"Telegram send failed, logged locally: {message_string}"
            )

    except Exception as e:
        LOGGER.error(f"Failed to send message via Telegram: {str(e)}")
        LOGGER.info(f"Message logged locally: {message_string}")


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
