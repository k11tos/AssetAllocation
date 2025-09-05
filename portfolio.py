#!/usr/bin/python3
"""
Get portfolio
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Tuple

import telegram
import yfinance as yf
from dotenv import load_dotenv
from fredapi import Fred

# Load environment variables
load_dotenv()

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# Constants for time periods (in trading days)
TRADING_DAYS_12_MONTHS = 252
TRADING_DAYS_6_MONTHS = 126
TRADING_DAYS_3_MONTHS = 63
TRADING_DAYS_1_MONTH = 21

# Momentum score weights
MOMENTUM_WEIGHTS = {"12_month": 1, "6_month": 2, "3_month": 4, "1_month": 12}


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
    Get ticker for HAA (Hybrid Asset Allocation)
    :param momentum_score_simple: Dictionary with simple momentum scores
    :return: Dictionary with asset allocation percentages
    """
    haa = {}

    attacker_dict = {
        "SPY": momentum_score_simple["SPY"],
        "IWM": momentum_score_simple["IWM"],
        "IEFA": momentum_score_simple["IEFA"],
        "IEMG": momentum_score_simple["IEMG"],
        "TLT": momentum_score_simple["TLT"],
        "IEF": momentum_score_simple["IEF"],
        "PDBC": momentum_score_simple["PDBC"],
        "VNQ": momentum_score_simple["VNQ"],
    }

    if momentum_score_simple["TIP"] > 0:
        attacker_profit_top4 = dict(
            sorted(attacker_dict.items(), key=lambda x: x[1], reverse=True)[:4]
        )
        for key in attacker_profit_top4.keys():
            haa[key] = 100.0 / 4
    elif momentum_score_simple["IEF"] > 0:
        haa["IEF"] = 100
    else:
        haa["CASH"] = 100

    return haa


def get_korean_all_weather_allocation() -> Dict[str, float]:
    """
    Get Korean All-Weather strategy allocation based on current month
    월말에 다음달의 전략을 수행하는 식으로 비율을 가져감 (4월 말에는 5월 전략)
    :return: Dictionary with asset allocation percentages
    """
    import datetime

    # 현재 날짜에서 다음 달을 계산
    today = datetime.datetime.now()
    next_month = today.month + 1 if today.month < 12 else 1

    # 한국형 올웨더 전략 비율 (11~4월 vs 5~10월)
    # 11~4월: 위험자산 중심, 5~10월: 안전자산 중심
    if next_month in [11, 12, 1, 2, 3, 4]:  # 11~4월 전략
        korean_all_weather = {
            "TIGER S&P500": 25.0,
            "KOSEF 200TR": 25.0,
            "KODEX 골드선물(H)": 15.0,
            "TIGER 미국채 10년 선물": 17.5,
            "KOSEF 국고채 10년": 17.5,
        }
    else:  # 5~10월 전략 (안전자산 중심)
        korean_all_weather = {
            "TIGER S&P500": 10.0,
            "KOSEF 200TR": 10.0,
            "KODEX 골드선물(H)": 15.0,
            "TIGER 미국채 10년 선물": 32.5,
            "KOSEF 국고채 10년": 32.5,
        }

    return korean_all_weather


def get_fred_account() -> Fred:
    """
    Initialize and return fred account
    """
    api_key = os.getenv("FRED_API_KEY")

    # Fallback to portfolio.txt if environment variable is not set
    if not api_key:
        try:
            with open("portfolio.txt", encoding="utf-8") as file_descriptor:
                lines = file_descriptor.readlines()
                api_key = lines[0].strip()
        except FileNotFoundError:
            LOGGER.error(
                "Neither FRED_API_KEY environment variable nor "
                "portfolio.txt file found."
            )
            sys.exit(1)

    try:
        fred_account = Fred(api_key=api_key)
        LOGGER.debug("Using FRED API is okay.")
        return fred_account
    except Exception as e:
        LOGGER.error("Failed to initialize the FRED account: %s", str(e))
        sys.exit(1)


def get_telegram_account(mode: str = "information") -> Dict:
    """
    Initialize and return telegram account
    """
    api_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    # Fallback to portfolio.txt if environment variables are not set
    if not api_token or not chat_id:
        try:
            with open("portfolio.txt", encoding="utf-8") as file_descriptor:
                lines = file_descriptor.readlines()
                api_token = lines[1].strip()
                chat_id = lines[2].strip()
        except (FileNotFoundError, IndexError):
            LOGGER.error(
                "Neither environment variables nor portfolio.txt file "
                "found for Telegram configuration."
            )
            sys.exit(1)

    try:
        if mode == "information":
            bot = telegram.Bot(api_token)
        elif mode == "conversation":
            bot = telegram.ext.Updater(token=api_token, use_context=True)
        else:
            LOGGER.error("Invalid mode for telegram bot")
            sys.exit(1)

        telegram_account = {"bot": bot, "chat_id": chat_id}
        LOGGER.debug("Using telegram API is okay.")
        return telegram_account
    except Exception as e:
        LOGGER.error("Failed to initialize the telegram account: %s", str(e))
        sys.exit(1)


def print_info_message(message_string: str) -> None:
    """
    Print info message by writing log or sending telegram messenger
    :param message_string: the message to print
    :return: None
    """
    telegram_account = get_telegram_account("information")
    telegram_bot = telegram_account["bot"]
    chat_id = telegram_account["chat_id"]

    try:
        asyncio.run(
            telegram_bot.sendMessage(chat_id=chat_id, text=message_string)
        )
    except telegram.TelegramError as error:
        LOGGER.error("Failed to send Telegram message: %s", str(error))
    else:
        LOGGER.info(message_string)


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
    Get financial data for given tickers
    :param tickers: space-separated string of ticker symbols
    :return: tuple of (momentum_score, momentum_score_simple,
                       profit_12month, profit_6month, sma_12month, today_price)
    """
    daily_price = {}
    momentum_score = {}
    momentum_score_simple = {}
    profit_12month = {}
    profit_6month = {}
    profit_3month = {}
    profit_1month = {}
    sma_12month = {}
    today_price = {}

    try:
        data = yf.download(
            tickers=tickers,
            period="1y",
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
        ).dropna()
    except Exception as e:
        LOGGER.error("Failed to download financial data: %s", str(e))
        raise ValueError(f"Failed to download financial data: {str(e)}")

    # Check if data is available
    if len(data) == 0:
        raise ValueError("No data available for the specified tickers")

    # Check if SPY data is available (used as reference)
    if ("SPY", "Adj Close") not in data.columns:
        raise ValueError("SPY data not available - required for calculations")

    # Get working days from SPY data (use Adj Close for adjusted prices)
    spy_adj_close = data[("SPY", "Adj Close")]
    working_day = len(spy_adj_close)

    for ticker in tickers.split():
        if (ticker, "Adj Close") not in data.columns:
            LOGGER.warning("No data available for ticker: %s", ticker)
            continue
        daily_price[ticker] = data[(ticker, "Adj Close")]
        profit_12month[ticker] = (
            daily_price[ticker].iloc[-1]
            - daily_price[ticker].iloc[-working_day]
        ) / daily_price[ticker].iloc[-1]
        profit_6month[ticker] = (
            daily_price[ticker].iloc[-1]
            - daily_price[ticker].iloc[-TRADING_DAYS_6_MONTHS]
        ) / daily_price[ticker].iloc[-1]
        profit_3month[ticker] = (
            daily_price[ticker].iloc[-1]
            - daily_price[ticker].iloc[-TRADING_DAYS_3_MONTHS]
        ) / daily_price[ticker].iloc[-1]
        profit_1month[ticker] = (
            daily_price[ticker].iloc[-1]
            - daily_price[ticker].iloc[-TRADING_DAYS_1_MONTH]
        ) / daily_price[ticker].iloc[-1]
        momentum_score[ticker] = (
            profit_12month[ticker] * MOMENTUM_WEIGHTS["12_month"]
            + profit_6month[ticker] * MOMENTUM_WEIGHTS["6_month"]
            + profit_3month[ticker] * MOMENTUM_WEIGHTS["3_month"]
            + profit_1month[ticker] * MOMENTUM_WEIGHTS["1_month"]
        )
        momentum_score_simple[ticker] = (
            profit_12month[ticker]
            + profit_6month[ticker]
            + profit_3month[ticker]
            + profit_1month[ticker]
        )
        sma_12month[ticker] = daily_price[ticker].mean()
        today_price[ticker] = daily_price[ticker].iloc[-1]

    return (
        momentum_score,
        momentum_score_simple,
        profit_12month,
        profit_6month,
        sma_12month,
        today_price,
    )
