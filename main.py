#!/usr/bin/python3
"""
Get portfolio with original dual momentum, VAA and LAA
"""

import asyncio
import datetime
import json

from portfolio import (
    get_bold_asset_allocation,
    get_bond_dynamic_asset_allocation,
    get_financial_data,
    get_hybrid_asset_allocation,
    get_modified_dual_momentum,
    print_info_message,
)


def main():
    """
    Main function
    :return: None
    """
    # BAA, modified dual momentum, Bond dynamic asset allocation
    total_number_of_strategy = 4

    # fred = get_fred_account()
    # sp500 = fred.get_series("SP500").dropna()
    # unrate = fred.get_series("UNRATE").dropna()
    with open("korean_etf.json", "r") as file:
        korean_etf = json.load(file)

    if korean_etf is None:
        raise ValueError
    tickers = korean_etf.keys()

    (
        momentum_score,
        momentum_score_simple,
        profit_12month,
        profit_6month,
        sma_12month,
        today_price,
    ) = get_financial_data(" ".join(tickers))

    asyncio.run(print_info_message(str(datetime.datetime.today().date())))

    baa = get_bold_asset_allocation(momentum_score, sma_12month, today_price)
    print_asset_allocation(baa, korean_etf, total_number_of_strategy, "<BAA>")

    mdm = get_modified_dual_momentum(profit_12month, profit_6month)
    print_asset_allocation(mdm, korean_etf, total_number_of_strategy, "<MDM>")

    bdaa = get_bond_dynamic_asset_allocation(profit_6month)
    print_asset_allocation(
        bdaa, korean_etf, total_number_of_strategy, "<BDAA>"
    )

    haa = get_hybrid_asset_allocation(momentum_score_simple)
    print_asset_allocation(haa, korean_etf, total_number_of_strategy, "<HAA>")


def print_asset_allocation(
    asset_allocation, korean_etf, total_number_of_strategy, strategy_name
):
    for key, value in asset_allocation.items():
        asyncio.run(
            print_info_message(
                f"{strategy_name} {korean_etf[key]} : "
                f"{round(value / total_number_of_strategy, 2)} %"
            )
        )


if __name__ == "__main__":
    main()
