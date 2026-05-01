#!/usr/bin/python3
"""
Data service for financial data retrieval
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
import talib as ta
import yfinance as yf
from fredapi import Fred

from config import (
    API_CONFIG,
    PRICE_PROVIDER_CONFIG,
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




class PriceProvider(ABC):
    """가격 제공자 인터페이스"""

    adjust_mode: str

    @abstractmethod
    def fetch(self, tickers: List[str]) -> pd.DataFrame:
        """티커별 조정 종가 데이터프레임을 반환합니다."""


class YahooPriceProvider(PriceProvider):
    adjust_mode = "adj_close"

    def fetch(self, tickers: List[str]) -> pd.DataFrame:
        ticker_str = " ".join(tickers)
        return yf.download(
            tickers=ticker_str,
            period=YFINANCE_CONFIG.PERIOD,
            interval=YFINANCE_CONFIG.INTERVAL,
            group_by="ticker",
            auto_adjust=YFINANCE_CONFIG.AUTO_ADJUST,
        ).dropna()


class TwelveDataPriceProvider(PriceProvider):
    adjust_mode = "all"
    base_url = "https://api.twelvedata.com/time_series"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _fetch_symbol(self, symbol: str) -> pd.Series:
        response = requests.get(
            self.base_url,
            params={
                "symbol": symbol,
                "interval": "1day",
                "outputsize": 400,
                "order": "ASC",
                "adjust": "all",
                "apikey": self.api_key,
            },
            timeout=YFINANCE_CONFIG.TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        if "values" not in payload:
            raise DataRetrievalError(
                f"Twelve Data response missing values for {symbol}: {payload}"
            )

        frame = pd.DataFrame(payload["values"])
        if "datetime" not in frame or "close" not in frame:
            raise DataRetrievalError(
                f"Twelve Data response missing datetime/close for {symbol}"
            )
        frame["datetime"] = pd.to_datetime(frame["datetime"])
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        series = frame.set_index("datetime")["close"].sort_index()
        return series

    def fetch(self, tickers: List[str]) -> pd.DataFrame:
        data = {symbol: self._fetch_symbol(symbol) for symbol in tickers}
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data).dropna(how="all").sort_index()

class DataService:
    """금융 데이터 서비스"""

    def __init__(self, cache_ttl_hours: int = 1):
        self.fred_account = None
        self.cache_manager = CacheManager(ttl_hours=cache_ttl_hours)
        self.security_manager = SecurityManager()
        self.last_market_data_date: Optional[str] = None
        self._initialize_fred()
        self.last_fetch_metadata: Dict[str, Any] = {}
        self.last_daily_prices: Dict[str, pd.Series] = {}

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

    def _extract_month_end_prices(
        self,
        price_series: pd.Series,
        drop_incomplete_current_month: bool = False,
        as_of_date: Optional[pd.Timestamp] = None,
    ) -> pd.Series:
        """일별 가격 시계열에서 월별 마지막 거래일 종가를 추출합니다.

        Args:
            price_series: 일별 가격 시계열
            drop_incomplete_current_month: True면 실행 기준 "현재 달" 그룹을 무조건 제거
            as_of_date: 진행 중인 달 판단 기준일(테스트용). 미지정 시 현재 날짜 사용
        """
        if price_series.empty:
            return price_series

        if not isinstance(price_series.index, pd.DatetimeIndex):
            return pd.Series(dtype=np.float64)

        period_index = price_series.index.to_period("M")
        month_end_prices = price_series.groupby(period_index).tail(1).copy()
        month_end_prices = month_end_prices.sort_index()

        if drop_incomplete_current_month and not month_end_prices.empty:
            reference_date = (
                pd.Timestamp(as_of_date) if as_of_date is not None else pd.Timestamp.now()
            )
            reference_date = reference_date.normalize()
            current_month = reference_date.to_period("M")

            latest_month = month_end_prices.index[-1].to_period("M")
            # HAA 운영 규칙: 현재 달은 절대 사용하지 않고, 다음 달이 시작된 뒤에만 유효.
            if latest_month == current_month:
                month_end_prices = month_end_prices.iloc[:-1]

        return month_end_prices

    def _calculate_month_end_returns(
        self, price_series: pd.Series, lookback_months: Tuple[int, ...] = (1, 3, 6, 12)
    ) -> Dict[int, float]:
        """월말 가격 시계열 기반으로 지정 개월 수 수익률을 계산합니다."""
        # HAA 의사결정은 "완료된 월" 기준이므로 현재 진행 중인 달은 제외한다.
        month_end_prices = self._extract_month_end_prices(
            price_series, drop_incomplete_current_month=True
        )
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
        provider_name = PRICE_PROVIDER_CONFIG.PROVIDER
        cache_key_params = {
            "period": YFINANCE_CONFIG.PERIOD,
            "interval": YFINANCE_CONFIG.INTERVAL,
            "auto_adjust": YFINANCE_CONFIG.AUTO_ADJUST,
            "provider": provider_name,
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

        data, evaluation_date = self._fetch_financial_data(validated_tickers, provider_name)
        self.last_market_data_date = evaluation_date

        # 캐시에 저장
        self.cache_manager.set(
            validated_tickers,
            {"result": data, "evaluation_date": evaluation_date},
            **cache_key_params,
        )

        return data

    def _fetch_financial_data(
        self, tickers: str, provider_name: str
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

        ticker_list = tickers.split()
        provider: PriceProvider
        if provider_name == "yahoo":
            provider = YahooPriceProvider()
        elif provider_name == "twelvedata":
            if not API_CONFIG.TWELVEDATA_API_KEY:
                raise DataValidationError(
                    "PRICE_PROVIDER=twelvedata requires TWELVEDATA_API_KEY. "
                    "Set TWELVEDATA_API_KEY in your environment or .env file."
                )
            provider = TwelveDataPriceProvider(API_CONFIG.TWELVEDATA_API_KEY)
        else:
            raise DataValidationError(f"Unsupported PRICE_PROVIDER: {provider_name}")

        try:
            raw_data = provider.fetch(ticker_list)
        except Exception as e:
            LOGGER.error(f"Failed to download financial data: {str(e)}")
            raise NetworkError(f"Failed to download financial data: {str(e)}")

        if len(raw_data) == 0:
            raise DataRetrievalError("No data available for the specified tickers")

        self.last_fetch_metadata = {
            "price_provider": provider_name,
            "adjust_mode": provider.adjust_mode,
            "symbols": ticker_list,
            "date_range": [str(raw_data.index.min().date()), str(raw_data.index.max().date())],
            "cached": False,
        }

        LOGGER.info("Price provider=%s adjust=%s symbols=%s date_range=%s", provider_name, provider.adjust_mode, ticker_list, self.last_fetch_metadata["date_range"])

        # 거래일 상수 가져오기
        trading_days = get_trading_days_dict()
        momentum_weights = get_momentum_weights_dict()

        # 각 티커에 대해 데이터 처리
        for ticker in ticker_list:
            if provider_name == "yahoo":
                if (ticker, "Adj Close") not in raw_data.columns:
                    LOGGER.warning(f"No data available for ticker: {ticker}")
                    continue
                daily_price[ticker] = raw_data[(ticker, "Adj Close")]
            else:
                if ticker not in raw_data.columns:
                    LOGGER.warning(f"No data available for ticker: {ticker}")
                    continue
                daily_price[ticker] = raw_data[ticker]

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

        self.last_daily_prices = daily_price
        LOGGER.info(
            f"✅ Successfully processed financial data for "
            f"{len(tickers.split())} tickers"
        )

        latest_index = raw_data.index[-1]
        haa_month_end_anchor: Optional[pd.Timestamp] = None
        for ticker in ticker_list:
            series = daily_price.get(ticker)
            if series is None:
                continue
            month_end_prices = self._extract_month_end_prices(
                series, drop_incomplete_current_month=True
            )
            if not month_end_prices.empty:
                haa_month_end_anchor = month_end_prices.index[-1]
                break

        anchor_index = haa_month_end_anchor if haa_month_end_anchor is not None else latest_index
        evaluation_date = (
            anchor_index.strftime("%Y-%m-%d")
            if hasattr(anchor_index, "strftime")
            else str(anchor_index)
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


    def get_tip_diagnostics(self, tip_series: Optional[pd.Series]) -> Dict[str, Any]:
        """HAA TIP 진단 정보 반환"""
        diagnostics: Dict[str, Any] = {
            "price_provider": self.last_fetch_metadata.get("price_provider", "unknown"),
            "adjust_mode": self.last_fetch_metadata.get("adjust_mode", "unknown"),
            "month_end_prices": {},
            "returns": {},
            "tip_13612u": 0.0,
            "canary_decision": "DEFENSIVE",
        }
        if tip_series is None or tip_series.empty:
            return diagnostics

        month_end = self._extract_month_end_prices(tip_series, drop_incomplete_current_month=True)
        labels = [(0, "T"), (1, "T-1"), (3, "T-3"), (6, "T-6"), (12, "T-12")]
        for offset, label in labels:
            if len(month_end) > offset:
                diagnostics["month_end_prices"][label] = float(month_end.iloc[-(offset+1)])

        returns = self._calculate_month_end_returns(tip_series)
        diagnostics["returns"] = {
            "1M": returns[1],
            "3M": returns[3],
            "6M": returns[6],
            "12M": returns[12],
        }
        diagnostics["tip_13612u"] = sum(diagnostics["returns"].values()) / 4.0
        diagnostics["canary_decision"] = "OFFENSIVE" if diagnostics["tip_13612u"] > 0 else "DEFENSIVE"
        return diagnostics

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
