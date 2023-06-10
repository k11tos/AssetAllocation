#!/usr/bin/python3
"""
Get portfolio with original dual momentum, VAA and LAA
"""

import datetime
import json
import logging
import sys
from collections import defaultdict

import telegram
import yfinance as yf
from fredapi import Fred

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_lethargic_asset_allocation(sp500, unrate):
    """
    Get ticker for LAA
    """
    laa = {"IWD": 25, "GLD": 25, "IEF": 25}

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


def get_original_dual_momentum(profit_12month):
    """
    Get ticker for original dual momentum
    """
    odm = {}

    LOGGER.debug("SPY 12 months average: %s", round(profit_12month["SPY"], 3))
    LOGGER.debug("BIL 12 months average: %s", round(profit_12month["BIL"], 3))
    LOGGER.debug("EFA 12 months average: %s", round(profit_12month["EFA"], 3))

    if profit_12month["SPY"] > profit_12month["BIL"]:
        if profit_12month["SPY"] >= profit_12month["EFA"]:
            odm["SPY"] = 100
        else:
            odm["EFA"] = 100
    else:
        odm["AGG"] = 100

    return odm


def get_vigilant_asset_allocation(momentum_score):
    """
    Get ticker for VAA
    """
    vaa = {}

    LOGGER.debug("Momentum Scores:")
    for ticker, score in momentum_score.items():
        LOGGER.debug(f"{ticker} momentum score: {round(score, 3)}")

    if all(score >= 0 for score in momentum_score.values()):
        attackers = ["SPY", "EFA", "EEM", "AGG"]
        attacker_ticker = max(attackers, key=lambda x: momentum_score[x])
        vaa[attacker_ticker] = 100
    else:
        defenders = ["LQD", "IEF", "SHY"]
        defender_ticker = max(defenders, key=lambda x: momentum_score[x])
        vaa[defender_ticker] = 100

    return vaa


def get_bold_asset_allocation(momentum_score, sma_12month, today_price):
    """
    Get ticker for BAA : 784
    """
    baa = {}

    canary = all(score >= 0 for score in momentum_score.values())
    if canary:
        attacker_momentum_score = {
            ticker: score
            for ticker, score in momentum_score.items()
            if ticker in ["QQQ", "EFA", "EEM", "AGG"]
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


def get_modifiled_dual_momentum(profit_12month, profit_6month):
    """
    Get ticker for MDM : 825
    """
    mdm = {}

    LOGGER.debug(
        "SPY 12 months average: %s", str(round(profit_12month["SPY"], 3))
    )
    LOGGER.debug(
        "EFA 12 months average: %s", str(round(profit_12month["EFA"], 3))
    )

    bonds = ["SHY", "IEF", "TLT", "TIP", "LQD", "HYG", "BWX", "EMB"]
    for bond in bonds:
        LOGGER.debug(
            "%s 6 months average: %s", bond, str(round(profit_6month[bond], 3))
        )

    if profit_12month["SPY"] > 0 or profit_12month["EFA"] > 0:
        if profit_12month["SPY"] >= profit_12month["EFA"]:
            mdm["SPY"] = 100
        else:
            mdm["EFA"] = 100
    else:
        mdm = get_bond_dynamic_asset_allocation(profit_6month)

    return mdm


def get_bond_dynamic_asset_allocation(profit_6month):
    """
    Get ticker for BDAA : 410
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


def get_hybrid_asset_allocation(momentum_score_simple):
    """
    Get ticker for HAA : 926
    """
    haa = {}

    attacker_dict = {
        "SPY": momentum_score_simple["SPY"],
        "IWM": momentum_score_simple["IWM"],
        "VEA": momentum_score_simple["VEA"],
        "VWO": momentum_score_simple["VWO"],
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


def get_fred_account():
    """
    Initialize and return fred account
    """
    fred_account = None

    with open("portfolio.txt", encoding="utf-8") as file_descriptor:
        lines = file_descriptor.readlines()
        api_key = lines[0].strip()
        fred_account = Fred(api_key=api_key)
        LOGGER.debug("Using FRED API is okay.")

    if fred_account is None:
        LOGGER.error("Failed to initialize the FRED account.")
        sys.exit()

    return fred_account


def get_telegram_account(mode="information"):
    """
    Initialize and return telegram account
    """

    with open("portfolio.txt", encoding="utf-8") as file_descriptor:
        lines = file_descriptor.readlines()
        api_token = lines[1].strip()
        chat_id = lines[2].strip()

        if mode == "information":
            bot = telegram.Bot(api_token)
        elif mode == "conversation":
            bot = telegram.ext.Updater(token=api_token, use_context=True)
        else:
            LOGGER.error("Invalid mode for telegram bot")
            sys.exit()

        telegram_account = {"bot": bot, "chat_id": chat_id}
        LOGGER.debug("Using telegram API is okay.")

    if telegram_account is None:
        LOGGER.error("Failed to initialize the telegram account.")
        sys.exit()

    return telegram_account


def print_info_message(message_string):
    """
    Print info message by writing log or sending telegram messenger
    :param message_string: the message to print
    :return: None
    """
    telegram_account = get_telegram_account("information")
    telegram_bot = telegram_account["bot"]
    chat_id = telegram_account["chat_id"]

    try:
        telegram_bot.sendMessage(chat_id=chat_id, text=message_string)
    except telegram.TelegramError as error:
        LOGGER.error("Failed to send Telegram message: %s", str(error))
    else:
        LOGGER.info(message_string)


def get_financial_data(tickers):
    """
    Get financial data
    :param
    :return:
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

    data = yf.download(
        tickers=tickers, period="1y", interval="1d", group_by="ticker"
    ).dropna()

    working_day = len(data["SPY"]["Adj Close"])

    for ticker in tickers.split():
        daily_price[ticker] = data[ticker]["Adj Close"]
        profit_12month[ticker] = (
            daily_price[ticker][-1] - daily_price[ticker][-working_day]
        ) / daily_price[ticker][-1]
        profit_6month[ticker] = (
            daily_price[ticker][-1] - daily_price[ticker][-126]
        ) / daily_price[ticker][-1]
        profit_3month[ticker] = (
            daily_price[ticker][-1] - daily_price[ticker][-63]
        ) / daily_price[ticker][-1]
        profit_1month[ticker] = (
            daily_price[ticker][-1] - daily_price[ticker][-21]
        ) / daily_price[ticker][-1]
        momentum_score[ticker] = (
            profit_12month[ticker] * 1
            + profit_6month[ticker] * 2
            + profit_3month[ticker] * 4
            + profit_1month[ticker] * 12
        )
        momentum_score_simple[ticker] = (
            profit_12month[ticker]
            + profit_6month[ticker]
            + profit_3month[ticker]
            + profit_1month[ticker]
        )
        sma_12month[ticker] = daily_price[ticker].mean()
        today_price[ticker] = daily_price[ticker][-1]

    return (
        momentum_score,
        momentum_score_simple,
        profit_12month,
        profit_6month,
        sma_12month,
        today_price,
    )


def main():
    """
    Main function
    :return: None
    """
    # BAA, modified dual momentum, Bond dynamic asset allocatio
    total_number_of_strategy = 4

    fred = get_fred_account()
    sp500 = fred.get_series("SP500").dropna()
    unrate = fred.get_series("UNRATE").dropna()
    with open("korean_etf.json", "r") as file:
        korean_etf = json.load(file)

    tickers = korean_etf.keys()

    (
        momentum_score,
        momentum_score_simple,
        profit_12month,
        profit_6month,
        sma_12month,
        today_price,
    ) = get_financial_data(" ".join(tickers))

    print_info_message(str(datetime.datetime.today().date()))
    # vaa = get_vigilant_asset_allocation(momentum_score)
    # for key, value in vaa.items():
    #     print_info_message(
    #         "<VAA> "
    #         + korean_etf[key]
    #         + " : "
    #         + str(round(value / total_number_of_strategy, 2))
    #         + " %"
    #     )
    # odm = get_original_dual_momentum(profit_12month)
    # for key, value in odm.items():
    #     print_info_message(
    #         "<ODM> "
    #         + korean_etf[key]
    #         + " : "
    #         + str(round(value / total_number_of_strategy, 2))
    #         + " %"
    #     )
    # laa = get_lethargic_asset_allocation(sp500, unrate)
    # for key, value in laa.items():
    #     if datetime.datetime.today().month == 1 or key not in [
    #         "IWD",
    #         "GLD",
    #         "IEF",
    #     ]:
    #         print_info_message(
    #             "<LAA> "
    #             + korean_etf[key]
    #             + " : "
    #             + str(round(value / total_number_of_strategy, 2))
    #             + " %"
    #         )
    # etf_ratio = defaultdict(int)
    # baa = get_bold_asset_allocation(momentum_score, sma_12month, today_price)
    # for key, value in baa.items():
    #     print_info_message(
    #         "<BAA> "
    #         + korean_etf[key]
    #         + " : "
    #         + str(round(value / total_number_of_strategy, 2))
    #         + " %"
    #     )
    # etf_ratio[key] = etf_ratio[key] + value / total_number_of_strategy
    # mdm = get_modifiled_dual_momentum(profit_12month, profit_6month)
    # for key, value in mdm.items():
    #     print_info_message(
    #         "<MDM> "
    #         + korean_etf[key]
    #         + " : "
    #         + str(round(value / total_number_of_strategy, 2))
    #         + " %"
    #     )
    #     etf_ratio[key] = etf_ratio[key] + value / total_number_of_strategy
    # bdaa = get_bond_dynamic_asset_allocation(profit_6month)
    # for key, value in bdaa.items():
    #     print_info_message(
    #         "<BDAA> "
    #         + korean_etf[key]
    #         + " : "
    #         + str(round(value / total_number_of_strategy, 2))
    #         + " %"
    #     )
    #     etf_ratio[key] = etf_ratio[key] + value / total_number_of_strategy
    haa = get_hybrid_asset_allocation(momentum_score_simple)
    for key, value in haa.items():
        print_info_message(
            "<HAA> "
            + korean_etf[key]
            + " : "
            + str(round(value / total_number_of_strategy, 2))
            + " %"
        )
    #     etf_ratio[key] = etf_ratio[key] + value / total_number_of_strategy
    #
    # for key, value in etf_ratio.items():
    #     print_info_message(
    #         korean_etf[key] + " : " + str(round(value, 2)) + " %"
    #     )


if __name__ == "__main__":
    main()
