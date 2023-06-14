#!/usr/bin/python3
"""
Get portfolio with original dual momentum, VAA and LAA
"""

import datetime
import json
from portfolio import (
    get_hybrid_asset_allocation,
    get_bold_asset_allocation,
    get_financial_data,
    print_info_message,
    get_bond_dynamic_asset_allocation,
    get_modifiled_dual_momentum,
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

    print_info_message(str(datetime.datetime.today().date()))

    baa = get_bold_asset_allocation(momentum_score, sma_12month, today_price)
    for key, value in baa.items():
        print_info_message(
            "<BAA> "
            + korean_etf[key]
            + " : "
            + str(round(value / total_number_of_strategy, 2))
            + " %"
        )
    # etf_ratio[key] = etf_ratio[key] + value / total_number_of_strategy
    mdm = get_modifiled_dual_momentum(profit_12month, profit_6month)
    for key, value in mdm.items():
        print_info_message(
            "<MDM> "
            + korean_etf[key]
            + " : "
            + str(round(value / total_number_of_strategy, 2))
            + " %"
        )
        # etf_ratio[key] = etf_ratio[key] + value / total_number_of_strategy
    bdaa = get_bond_dynamic_asset_allocation(profit_6month)
    for key, value in bdaa.items():
        print_info_message(
            "<BDAA> "
            + korean_etf[key]
            + " : "
            + str(round(value / total_number_of_strategy, 2))
            + " %"
        )
        # etf_ratio[key] = etf_ratio[key] + value / total_number_of_strategy
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
