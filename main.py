#!/usr/bin/python3
"""
Get portfolio with original dual momentum, VAA and LAA
"""

import datetime
import json
import logging
from typing import Dict

from portfolio import (
    get_bold_asset_allocation,
    get_bond_dynamic_asset_allocation,
    get_financial_data,
    get_fred_account,
    get_hybrid_asset_allocation,
    get_lethargic_asset_allocation,
    get_modified_dual_momentum,
    print_info_message,
)

LOGGER = logging.getLogger(__name__)


def main() -> None:
    """
    Main function
    :return: None
    """
    # BAA, modified dual momentum, Bond dynamic asset allocation
    total_number_of_strategy = 1

    # Get FRED data for LAA strategy (currently disabled)
    # try:
    #     fred = get_fred_account()
    #     sp500 = fred.get_series("SP500").dropna()
    #     unrate = fred.get_series("UNRATE").dropna()
    # except Exception as e:
    #     LOGGER.warning(
    #         "Failed to get FRED data: %s. Skipping LAA strategy.",
    #         str(e)
    #     )
    #     sp500 = None
    #     unrate = None
    with open("korean_etf.json", "r", encoding="utf-8") as file:
        korean_etf = json.load(file)

    if korean_etf is None:
        raise ValueError

    # korean_etf를 사용하지 않고 미국 ETF 데이터를 사용하기 위해,
    # korean_etf의 key와 value를 대체합니다.
    korean_etf = {key: key for key in korean_etf.keys()}
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

    # baa = get_bold_asset_allocation(
    #     momentum_score, sma_12month, today_price
    # )
    # print_asset_allocation(
    #     baa, korean_etf, total_number_of_strategy, "<BAA>"
    # )

    # mdm = get_modified_dual_momentum(profit_12month, profit_6month)
    # print_asset_allocation(
    #     mdm, korean_etf, total_number_of_strategy, "<MDM>"
    # )

    # bdaa = get_bond_dynamic_asset_allocation(profit_6month)
    # print_asset_allocation(
    #     bdaa, korean_etf, total_number_of_strategy, "<BDAA>"
    # )

    haa = get_hybrid_asset_allocation(momentum_score_simple)
    print_asset_allocation(haa, korean_etf, total_number_of_strategy, "<HAA>")

    # # LAA strategy requires FRED data
    # if sp500 is not None and unrate is not None:
    #     laa = get_lethargic_asset_allocation(sp500, unrate)
    #     print_asset_allocation(
    #         laa, korean_etf, total_number_of_strategy, "<LAA>"
    #     )
    # else:
    #     LOGGER.info("Skipping LAA strategy due to missing FRED data")


def print_asset_allocation(
    asset_allocation: Dict[str, float],
    korean_etf: Dict[str, str],
    total_number_of_strategy: int,
    strategy_name: str,
) -> None:
    """
    Print asset allocation results
    :param asset_allocation: Dictionary with asset allocation
    :param korean_etf: Dictionary mapping tickers to descriptions
    :param total_number_of_strategy: Total number of strategies
    :param strategy_name: Name of the strategy
    :return: None
    """
    for key, value in asset_allocation.items():
        print_info_message(
            f"{strategy_name} {korean_etf[key]}: "
            f"{round(value / total_number_of_strategy, 2)} %"
        )


if __name__ == "__main__":
    main()
