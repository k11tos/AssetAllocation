#!/usr/bin/python3
"""
Portfolio management module - refactored for better structure
"""

import logging
from typing import Dict, Tuple

# Load environment variables
from dotenv import load_dotenv

from services.communication_service import CommunicationService
from services.data_service import DataService
from strategies import HAAStrategy, KoreanAllWeatherStrategy

load_dotenv()

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


def get_lethargic_asset_allocation(sp500, unrate) -> Dict[str, float]:
    """
    Get ticker for LAA (Lethargic Asset Allocation)
    :param sp500: S&P 500 time series data from FRED
    :param unrate: Unemployment rate time series data from FRED
    :return: Dictionary with asset allocation percentages
    """
    laa = {"VTV": 25, "GLD": 25, "IEF": 25}

    sp500_average_200days = sp500.rolling(138).mean().iloc[-1]
    unrate_average_12months = unrate.rolling(12).mean().iloc[-1]

    LOGGER.debug("S&P500 200 days average: %s", round(sp500_average_200days))
    LOGGER.debug("S&P500 today: %s", round(sp500.iloc[-1]))
    LOGGER.debug(
        "Unemployment rate 12 months average: %s",
        round(unrate_average_12months, 1),
    )
    LOGGER.debug("Unemployment rate this month: %s", round(unrate.iloc[-1], 1))

    if (
        sp500_average_200days > sp500.iloc[-1]
        and unrate_average_12months < unrate.iloc[-1]
    ):
        laa["SHY"] = 25
    else:
        laa["QQQ"] = 25

    return laa


def get_original_dual_momentum(
    profit_12month: Dict[str, float]
) -> Dict[str, float]:
    """
    Get ticker for original dual momentum
    :param profit_12month: Dictionary with 12-month profit data
    :return: Dictionary with asset allocation percentages
    """
    odm = {}

    LOGGER.debug("SPY 12 months average: %s", round(profit_12month["SPY"], 3))
    LOGGER.debug("BIL 12 months average: %s", round(profit_12month["BIL"], 3))
    LOGGER.debug(
        "IEFA 12 months average: %s", round(profit_12month["IEFA"], 3)
    )

    if profit_12month["SPY"] > profit_12month["BIL"]:
        if profit_12month["SPY"] >= profit_12month["IEFA"]:
            odm["SPY"] = 100
        else:
            odm["IEFA"] = 100
    else:
        odm["AGG"] = 100

    return odm


def get_vigilant_asset_allocation(
    momentum_score: Dict[str, float]
) -> Dict[str, float]:
    """
    Get ticker for VAA (Vigilant Asset Allocation)
    :param momentum_score: Dictionary with momentum scores
    :return: Dictionary with asset allocation percentages
    """
    vaa = {}

    LOGGER.debug("Momentum Scores:")
    for ticker, score in momentum_score.items():
        LOGGER.debug("%s momentum score: %s", ticker, round(score, 3))

    if all(score >= 0 for score in momentum_score.values()):
        attackers = ["SPY", "IEFA", "IEMG", "AGG"]
        attacker_ticker = max(attackers, key=lambda x: momentum_score[x])
        vaa[attacker_ticker] = 100
    else:
        defenders = ["LQD", "IEF", "SHY"]
        defender_ticker = max(defenders, key=lambda x: momentum_score[x])
        vaa[defender_ticker] = 100

    return vaa


def get_bold_asset_allocation(
    momentum_score: Dict[str, float],
    sma_12month: Dict[str, float],
    today_price: Dict[str, float],
) -> Dict[str, float]:
    """
    Get ticker for BAA (Bold Asset Allocation)
    :param momentum_score: Dictionary with momentum scores
    :param sma_12month: Dictionary with 12-month moving averages
    :param today_price: Dictionary with current prices
    :return: Dictionary with asset allocation percentages
    """
    baa = {}

    canary = all(score >= 0 for score in momentum_score.values())
    if canary:
        attacker_momentum_score = {
            ticker: score
            for ticker, score in momentum_score.items()
            if ticker in ["QQQ", "IEFA", "IEMG", "AGG"]
        }
        top_attacker = max(
            attacker_momentum_score, key=attacker_momentum_score.get
        )
        baa[top_attacker] = 100.0
    else:
        defenders = ["BIL", "IEF", "TLT", "LQD", "TIP", "BND", "DBC"]
        price_index = {
            defender: today_price[defender] / sma_12month[defender]
            for defender in defenders
        }
        top_defenders = dict(
            sorted(price_index.items(), key=lambda x: x[1], reverse=True)[:3]
        )
        bil = 0.0
        for defender in top_defenders.keys():
            if (
                defender == "BIL"
                or today_price[defender] < sma_12month[defender]
            ):
                bil += 100.0 / 3
            else:
                baa[defender] = 100.0 / 3
        if bil != 0:
            baa["BIL"] = bil

    return baa


def get_modified_dual_momentum(
    profit_12month: Dict[str, float], profit_6month: Dict[str, float]
) -> Dict[str, float]:
    """
    Get ticker for MDM (Modified Dual Momentum)
    :param profit_12month: Dictionary with 12-month profit data
    :param profit_6month: Dictionary with 6-month profit data
    :return: Dictionary with asset allocation percentages
    """
    mdm = {}

    LOGGER.debug(
        "SPY 12 months average: %s", str(round(profit_12month["SPY"], 3))
    )
    LOGGER.debug(
        "IEFA 12 months average: %s", str(round(profit_12month["IEFA"], 3))
    )

    bonds = ["SHY", "IEF", "TLT", "TIP", "LQD", "HYG", "BWX", "EMB"]
    for bond in bonds:
        LOGGER.debug(
            "%s 6 months average: %s", bond, str(round(profit_6month[bond], 3))
        )

    if profit_12month["SPY"] > 0 or profit_12month["IEFA"] > 0:
        if profit_12month["SPY"] >= profit_12month["IEFA"]:
            mdm["SPY"] = 100
        else:
            mdm["IEFA"] = 100
    else:
        mdm = get_bond_dynamic_asset_allocation(profit_6month)

    return mdm


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
    )[:3]

    cash = 0
    for key, value in bond_profit_top3:
        if value < 0:
            cash += 100.0 / 3
        else:
            bdaa[key] = 100.0 / 3

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


# Legacy functions for backward compatibility
def get_fred_account():
    """레거시 함수 - DataService를 사용하세요."""
    LOGGER.warning("get_fred_account is deprecated, use DataService instead")
    return get_data_service().fred_account


def get_telegram_account(mode: str = "information"):
    """레거시 함수 - CommunicationService를 사용하세요."""
    LOGGER.warning(
        "get_telegram_account is deprecated, use CommunicationService instead"
    )
    communication_service = get_communication_service()
    return {
        "bot": communication_service.get_telegram_bot(mode),
        "chat_id": communication_service.telegram_account["chat_id"]
        if communication_service.telegram_account
        else None,
    }


def print_info_message(message_string: str) -> None:
    """
    정보 메시지를 출력하고 텔레그램으로 전송합니다.

    Args:
        message_string: 출력할 메시지
    """
    communication_service = get_communication_service()

    # 텔레그램으로 전송 시도
    success = communication_service.send_message(message_string)

    # 전송 실패 시 로그에만 기록
    if not success:
        LOGGER.info(message_string)
    else:
        LOGGER.debug(f"Message sent via Telegram: {message_string[:50]}...")


# Global service instances
_data_service = None
_communication_service = None


def get_data_service() -> DataService:
    """데이터 서비스 인스턴스를 반환합니다."""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service


def get_communication_service() -> CommunicationService:
    """통신 서비스 인스턴스를 반환합니다."""
    global _communication_service
    if _communication_service is None:
        _communication_service = CommunicationService()
    return _communication_service


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
