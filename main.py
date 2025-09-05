#!/usr/bin/python3
"""
Get portfolio with original dual momentum, VAA and LAA
"""

import datetime
import json
import logging
from typing import Dict

from portfolio import (
    get_financial_data,
    get_hybrid_asset_allocation,
    get_korean_all_weather_allocation,
    print_info_message,
)

LOGGER = logging.getLogger(__name__)


def main() -> None:
    """
    Main function
    :return: None
    """
    total_number_of_strategy = 2

    with open("us_etf_tickers.json", "r", encoding="utf-8") as file:
        tickers = json.load(file)

    if not tickers:
        raise ValueError("No tickers found in us_etf_tickers.json")

    # tickers를 딕셔너리로 변환 (출력용)
    etf_descriptions = {ticker: ticker for ticker in tickers}

    print_info_message(str(datetime.datetime.today().date()))

    # 한국형 올웨더 전략 (가격 데이터 불필요)
    korean_all_weather = get_korean_all_weather_allocation()

    # HAA 전략을 위한 가격 데이터 가져오기 (실패 시 기본값 사용)
    try:
        (
            momentum_score,
            momentum_score_simple,
            profit_12month,
            profit_6month,
            sma_12month,
            today_price,
        ) = get_financial_data(" ".join(tickers))

        # HAA 전략
        haa = get_hybrid_asset_allocation(momentum_score_simple)
        print_asset_allocation(
            haa, etf_descriptions, total_number_of_strategy, "[HAA]"
        )

    except Exception as e:
        LOGGER.warning(
            f"Failed to get financial data for HAA strategy: {str(e)}"
        )

    # 한국형 올웨더 전략 (HAA 성공/실패와 관계없이 항상 실행)
    print_asset_allocation(
        korean_all_weather, None, total_number_of_strategy, "[KAW]"
    )


def print_asset_allocation(
    asset_allocation: Dict[str, float],
    etf_descriptions: Dict[str, str],
    total_number_of_strategy: int,
    strategy_name: str,
) -> None:
    """
    Print asset allocation results
    :param asset_allocation: Dictionary with asset allocation
    :param etf_descriptions: Dictionary mapping tickers to descriptions
    :param total_number_of_strategy: Total number of strategies
    :param strategy_name: Name of the strategy
    :return: None
    """
    if etf_descriptions is not None:
        for key, value in asset_allocation.items():
            print_info_message(
                f"{strategy_name} {etf_descriptions[key]}: "
                f"{round(value / total_number_of_strategy, 2)} %"
            )
    else:
        for key, value in asset_allocation.items():
            print_info_message(
                f"{strategy_name} {key}: "
                f"{round(value / total_number_of_strategy, 2)} %"
            )


if __name__ == "__main__":
    main()
