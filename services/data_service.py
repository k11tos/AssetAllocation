#!/usr/bin/python3
"""
Data service for financial data retrieval
"""

import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import talib as ta
import yfinance as yf
from fredapi import Fred

from config import (
    API_CONFIG,
    YFINANCE_CONFIG,
    get_momentum_weights_dict,
    get_trading_days_dict,
)
from exceptions import DataRetrievalError, DataValidationError, NetworkError
from utils.cache_manager import CacheManager
from utils.logging_config import LoggingConfig
from utils.performance_monitor import monitor_performance
from utils.security import InputValidator, SecurityManager, log_security_event

LOGGER = LoggingConfig.get_logger(__name__)


class DataService:
    """금융 데이터 서비스"""

    def __init__(self, cache_ttl_hours: int = 1):
        self.fred_account = None
        self.cache_manager = CacheManager(ttl_hours=cache_ttl_hours)
        self.security_manager = SecurityManager()
        self.last_market_data_date: Optional[str] = None
        self._initialize_fred()

    def get_last_market_data_date(self) -> Optional[str]:
        """가장 최근 get_financial_data 실행의 시장 데이터 기준일을 반환합니다."""
        return self.last_market_data_date

    def _initialize_fred(self) -> None:
        """FRED 계정을 초기화합니다."""
        try:
            api_key = API_CONFIG.FRED_API_KEY

            # Fallback to portfolio.txt if environment variable is not set
            if not api_key:
                try:
                    if not InputValidator.validate_file_path(
                        API_CONFIG.FALLBACK_FILE
                    ):
                        raise ValueError("Invalid fallback file path")

                    with open(
                        API_CONFIG.FALLBACK_FILE, encoding="utf-8"
                    ) as file_descriptor:
                        lines = file_descriptor.readlines()
                        api_key = lines[0].strip()
                except FileNotFoundError:
                    LOGGER.error(
                        f"Neither FRED_API_KEY environment variable nor "
                        f"{API_CONFIG.FALLBACK_FILE} file found."
                    )
                    raise

            # API 키 형식 검증
            if not self.security_manager.validate_api_key_format(
                api_key, "fred"
            ):
                log_security_event(
                    "INVALID_API_KEY", "Invalid FRED API key format", "ERROR"
                )
                raise ValueError("Invalid FRED API key format")

            self.fred_account = Fred(api_key=api_key)
            LOGGER.debug("🔑 FRED API initialized successfully")
            log_security_event(
                "API_INITIALIZED", "FRED API initialized successfully"
            )

        except Exception as e:
            LOGGER.error(f"Failed to initialize FRED account: {str(e)}")
            log_security_event(
                "API_INIT_FAILED",
                f"FRED API initialization failed: {str(e)}",
                "ERROR",
            )
            raise

    def _extract_month_end_prices(self, price_series: pd.Series) -> pd.Series:
        """일별 가격 시계열에서 월말(해당 월의 마지막 거래일) 종가를 추출합니다."""
        if price_series.empty:
            return price_series

        if not isinstance(price_series.index, pd.DatetimeIndex):
            return pd.Series(dtype=np.float64)

        month_end_prices = price_series.groupby(
            price_series.index.to_period("M")
        ).last()
        month_end_prices.index = month_end_prices.index.to_timestamp("M")

        return month_end_prices

    def _calculate_month_end_returns(
        self, price_series: pd.Series, lookback_months: Tuple[int, ...] = (1, 3, 6, 12)
    ) -> Dict[int, float]:
        """월말 가격 시계열 기반으로 지정 개월 수 수익률을 계산합니다."""
        month_end_prices = self._extract_month_end_prices(price_series)
        returns: Dict[int, float] = {}

        if month_end_prices.empty:
            return {months: 0.0 for months in lookback_months}

        latest_price = month_end_prices.iloc[-1]
        for months in lookback_months:
            if len(month_end_prices) <= months:
                returns[months] = 0.0
                continue

            past_price = month_end_prices.iloc[-(months + 1)]
            if past_price == 0 or np.isnan(past_price) or np.isnan(latest_price):
                returns[months] = 0.0
            else:
                returns[months] = (latest_price / past_price) - 1.0

        return returns

    @monitor_performance("get_financial_data")
    def get_financial_data(
        self, tickers: str
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
        캐싱을 통해 성능을 최적화합니다.

        Args:
            tickers: 공백으로 구분된 티커 심볼 문자열

        Returns:
            (momentum_score, momentum_score_simple, profit_12month,
             profit_6month, sma_12month, today_price) 튜플
        """
        # 입력 검증
        if not tickers or not isinstance(tickers, str):
            raise DataValidationError("Invalid tickers input")

        # 티커 목록 검증
        ticker_list = tickers.split()
        valid_tickers = self.security_manager.validate_ticker_list(ticker_list)

        if not valid_tickers:
            raise DataValidationError("No valid tickers provided")

        if len(valid_tickers) != len(ticker_list):
            log_security_event(
                "INVALID_TICKERS",
                f"Some tickers were invalid: {ticker_list}",
                "WARNING",
            )

        # 검증된 티커로 다시 조합
        validated_tickers = " ".join(valid_tickers)

        # 캐시에서 데이터 확인
        cache_key_params = {
            "period": YFINANCE_CONFIG.PERIOD,
            "interval": YFINANCE_CONFIG.INTERVAL,
            "auto_adjust": YFINANCE_CONFIG.AUTO_ADJUST,
        }

        cached_data = self.cache_manager.get(
            validated_tickers, **cache_key_params
        )
        if cached_data is not None:
            LoggingConfig.log_data_retrieval(
                LOGGER, "cache", valid_tickers, cached=True
            )
            if isinstance(cached_data, dict) and "result" in cached_data:
                self.last_market_data_date = cached_data.get("evaluation_date")
                return cached_data["result"]
            if isinstance(cached_data, tuple):
                # 레거시 캐시 포맷: 기준일 정보가 없으므로 재조회 후 캐시 갱신
                LOGGER.debug(
                    "Legacy cache format detected; refreshing to capture evaluation date"
                )

        LoggingConfig.log_data_retrieval(
            LOGGER, "yfinance", valid_tickers, cached=False
        )
        data, evaluation_date = self._fetch_financial_data(validated_tickers)
        self.last_market_data_date = evaluation_date

        # 캐시에 저장
        self.cache_manager.set(
            validated_tickers,
            {"result": data, "evaluation_date": evaluation_date},
            **cache_key_params,
        )

        return data

    def _fetch_financial_data(
        self, tickers: str
    ) -> Tuple[
        Tuple[
            Dict[str, float],
            Dict[str, float],
            Dict[str, float],
            Dict[str, float],
            Dict[str, float],
            Dict[str, float],
        ],
        str,
    ]:
        """
        실제 금융 데이터를 가져옵니다.

        Args:
            tickers: 공백으로 구분된 티커 심볼 문자열

        Returns:
            (momentum_score, momentum_score_simple, profit_12month,
             profit_6month, sma_12month, today_price) 튜플
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
                period=YFINANCE_CONFIG.PERIOD,
                interval=YFINANCE_CONFIG.INTERVAL,
                group_by="ticker",
                auto_adjust=YFINANCE_CONFIG.AUTO_ADJUST,
            ).dropna()
        except Exception as e:
            LOGGER.error(f"Failed to download financial data: {str(e)}")
            raise NetworkError(f"Failed to download financial data: {str(e)}")

        # 데이터 유효성 검사
        if len(data) == 0:
            raise DataRetrievalError(
                "No data available for the specified tickers"
            )

        # 첫 번째 자산을 기준으로 거래일 수 계산
        first_ticker = data.columns.get_level_values(0)[0]
        if (first_ticker, "Adj Close") not in data.columns:
            raise DataRetrievalError(
                f"{first_ticker} data not available "
                "- required for calculations"
            )

        # 거래일 상수 가져오기
        trading_days = get_trading_days_dict()
        momentum_weights = get_momentum_weights_dict()

        # 각 티커에 대해 데이터 처리
        for ticker in tickers.split():
            if (ticker, "Adj Close") not in data.columns:
                LOGGER.warning(f"No data available for ticker: {ticker}")
                continue

            daily_price[ticker] = data[(ticker, "Adj Close")]

            # 수익률 계산 (ta-lib ROC 사용)
            # ta-lib는 double 타입을 요구하므로 astype으로 변환
            price_array = daily_price[ticker].values.astype(np.float64)

            # 12개월 수익률 (ROC는 백분율로 반환되므로 100으로 나눔)
            roc_12month = ta.ROC(
                price_array, timeperiod=trading_days["12_month"]
            )
            profit_12month[ticker] = (
                roc_12month[-1] / 100.0
                if not np.isnan(roc_12month[-1])
                else 0.0
            )

            # 6개월 수익률
            roc_6month = ta.ROC(
                price_array, timeperiod=trading_days["6_month"]
            )
            profit_6month[ticker] = (
                roc_6month[-1] / 100.0 if not np.isnan(roc_6month[-1]) else 0.0
            )

            # 3개월 수익률
            roc_3month = ta.ROC(
                price_array, timeperiod=trading_days["3_month"]
            )
            profit_3month[ticker] = (
                roc_3month[-1] / 100.0 if not np.isnan(roc_3month[-1]) else 0.0
            )

            # 1개월 수익률
            roc_1month = ta.ROC(
                price_array, timeperiod=trading_days["1_month"]
            )
            profit_1month[ticker] = (
                roc_1month[-1] / 100.0 if not np.isnan(roc_1month[-1]) else 0.0
            )

            # 모멘텀 스코어 계산
            momentum_score[ticker] = (
                profit_12month[ticker] * momentum_weights["12_month"]
                + profit_6month[ticker] * momentum_weights["6_month"]
                + profit_3month[ticker] * momentum_weights["3_month"]
                + profit_1month[ticker] * momentum_weights["1_month"]
            )

            # HAA 단순 모멘텀(13612U): 월말 기준 1/3/6/12개월 수익률의 동일가중 평균
            month_end_returns = self._calculate_month_end_returns(
                daily_price[ticker]
            )
            momentum_score_simple[ticker] = (
                month_end_returns[12]
                + month_end_returns[6]
                + month_end_returns[3]
                + month_end_returns[1]
            ) / 4.0

            # 12개월 단순이동평균 계산 (ta-lib SMA 사용)
            sma_12month[ticker] = ta.SMA(
                price_array, timeperiod=trading_days["12_month"]
            )[-1]
            today_price[ticker] = daily_price[ticker].iloc[-1]

        LOGGER.info(
            f"✅ Successfully processed financial data for "
            f"{len(tickers.split())} tickers"
        )

        latest_index = data.index[-1]
        evaluation_date = (
            latest_index.strftime("%Y-%m-%d")
            if hasattr(latest_index, "strftime")
            else str(latest_index)
        )
        return (
            (
                momentum_score,
                momentum_score_simple,
                profit_12month,
                profit_6month,
                sma_12month,
                today_price,
            ),
            evaluation_date,
        )

    @monitor_performance("get_fred_data")
    def get_fred_data(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """
        FRED에서 데이터를 가져옵니다.

        Args:
            series_id: FRED 시리즈 ID
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)

        Returns:
            FRED 데이터 시리즈
        """
        try:
            if self.fred_account is None:
                raise DataRetrievalError("FRED account not initialized")

            data = self.fred_account.get_series(
                series_id, start_date, end_date
            )
            LOGGER.debug(f"Successfully retrieved FRED data for {series_id}")
            return data

        except DataRetrievalError:
            # 이미 정의된 예외는 그대로 전파
            raise
        except Exception as e:
            LOGGER.error(f"Failed to get FRED data for {series_id}: {str(e)}")
            raise DataRetrievalError(
                f"Failed to get FRED data for {series_id}: {str(e)}"
            ) from e

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계를 반환합니다."""
        return self.cache_manager.get_cache_stats()

    def clear_cache(self, older_than_hours: int = 24) -> int:
        """오래된 캐시를 정리합니다."""
        return self.cache_manager.clear(older_than_hours)
