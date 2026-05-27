#!/usr/bin/python3
"""
Configuration settings for asset allocation strategies
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()


def _get_positive_int_env(var_name: str, default: int) -> int:
    """양의 정수 환경변수를 안전하게 파싱합니다."""
    raw_value = os.getenv(var_name)
    if raw_value is None:
        return default

    try:
        parsed = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{var_name} must be a positive integer (e.g., {default})."
        ) from exc

    if parsed <= 0:
        raise ValueError(f"{var_name} must be greater than 0.")

    return parsed



SCHEDULED_STRATEGIES = ["HAA", "KAW", "SECTOR_MOMENTUM"]
SCHEDULED_STRATEGY_WEIGHTS = {"HAA": 45.0, "KAW": 45.0, "SECTOR_MOMENTUM": 10.0}

class KoreanAllWeatherConstants:
    """한국형 올웨더 전략 상수들"""

    # 위험자산 중심 기간 배분
    RISKY_EQUITY_ALLOCATION = 25.0
    RISKY_GOLD_ALLOCATION = 15.0
    RISKY_BOND_ALLOCATION = 17.5

    # 안전자산 중심 기간 배분
    SAFE_EQUITY_ALLOCATION = 10.0
    SAFE_GOLD_ALLOCATION = 15.0
    SAFE_BOND_ALLOCATION = 32.5

    # 위험자산 중심 기간 (11~4월)
    RISKY_MONTHS = [11, 12, 1, 2, 3, 4]


@dataclass
class TradingDays:
    """거래일 상수"""

    MONTH_1: int = 21
    MONTH_3: int = 63
    MONTH_6: int = 126
    MONTH_12: int = 252


@dataclass
class MomentumWeights:
    """모멘텀 가중치"""

    MONTH_12: int = 1
    MONTH_6: int = 2
    MONTH_3: int = 4
    MONTH_1: int = 12


@dataclass
class StrategyConfig:
    """전략별 설정"""

    TICKER_FILE: str = "us_etf_tickers.json"
    LOG_FILE: str = "logs/asset_allocation.log"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


@dataclass
class KoreanAllWeatherConfig:
    """한국형 올웨더 전략 설정"""

    # 11~4월 전략 (위험자산 중심)
    RISKY_PERIOD_ALLOCATION: Optional[Dict[str, float]] = None

    # 5~10월 전략 (안전자산 중심)
    SAFE_PERIOD_ALLOCATION: Optional[Dict[str, float]] = None

    # 위험자산 중심 기간 (11~4월)
    RISKY_MONTHS: Optional[List[int]] = None

    def __post_init__(self):
        if self.RISKY_PERIOD_ALLOCATION is None:
            self.RISKY_PERIOD_ALLOCATION = {
                "TIGER S&P500": (
                    KoreanAllWeatherConstants.RISKY_EQUITY_ALLOCATION
                ),
                "KOSEF 200TR": (
                    KoreanAllWeatherConstants.RISKY_EQUITY_ALLOCATION
                ),
                "KODEX 골드선물(H)": (
                    KoreanAllWeatherConstants.RISKY_GOLD_ALLOCATION
                ),
                "TIGER 미국채 10년 선물": (
                    KoreanAllWeatherConstants.RISKY_BOND_ALLOCATION
                ),
                "KOSEF 국고채 10년": (
                    KoreanAllWeatherConstants.RISKY_BOND_ALLOCATION
                ),
            }

        if self.SAFE_PERIOD_ALLOCATION is None:
            self.SAFE_PERIOD_ALLOCATION = {
                "TIGER S&P500": (
                    KoreanAllWeatherConstants.SAFE_EQUITY_ALLOCATION
                ),
                "KOSEF 200TR": (
                    KoreanAllWeatherConstants.SAFE_EQUITY_ALLOCATION
                ),
                "KODEX 골드선물(H)": (
                    KoreanAllWeatherConstants.SAFE_GOLD_ALLOCATION
                ),
                "TIGER 미국채 10년 선물": (
                    KoreanAllWeatherConstants.SAFE_BOND_ALLOCATION
                ),
                "KOSEF 국고채 10년": (
                    KoreanAllWeatherConstants.SAFE_BOND_ALLOCATION
                ),
            }

        if self.RISKY_MONTHS is None:
            self.RISKY_MONTHS = KoreanAllWeatherConstants.RISKY_MONTHS


@dataclass
class HAAConfig:
    """HAA (Hybrid Asset Allocation) 전략 설정"""

    OFFENSIVE_TICKERS: Optional[List[str]] = None
    DEFENSIVE_TICKERS: Optional[List[str]] = None
    CANARY_TICKERS: Optional[List[str]] = None
    ATTACKER_TICKERS: Optional[List[str]] = None
    TIP_THRESHOLD: float = 0.0
    IEF_THRESHOLD: float = 0.0
    TOP_ATTACKERS_COUNT: int = 4

    def __post_init__(self):
        if self.OFFENSIVE_TICKERS is None:
            self.OFFENSIVE_TICKERS = [
                "SPY",
                "IWM",
                "IEFA",
                "IEMG",
                "VNQ",
                "PDBC",
                "IEF",
                "TLT",
            ]
        if self.DEFENSIVE_TICKERS is None:
            self.DEFENSIVE_TICKERS = ["BIL", "IEF"]
        if self.CANARY_TICKERS is None:
            self.CANARY_TICKERS = ["TIP"]

        # 하위 호환성: 기존 ATTACKER_TICKERS는 OFFENSIVE_TICKERS와 동일하게 유지
        if self.ATTACKER_TICKERS is None:
            self.ATTACKER_TICKERS = self.OFFENSIVE_TICKERS


@dataclass
class VAAConfig:
    """VAA (Vigilant Asset Allocation) 전략 설정"""

    ATTACKER_TICKERS: Optional[List[str]] = None
    DEFENDER_TICKERS: Optional[List[str]] = None

    def __post_init__(self):
        if self.ATTACKER_TICKERS is None:
            self.ATTACKER_TICKERS = ["SPY", "IEFA", "IEMG", "AGG"]
        if self.DEFENDER_TICKERS is None:
            self.DEFENDER_TICKERS = ["LQD", "IEF", "SHY"]


@dataclass
class BAAConfig:
    """BAA (Bold Asset Allocation) 전략 설정"""

    ATTACKER_TICKERS: Optional[List[str]] = None
    DEFENDER_TICKERS: Optional[List[str]] = None
    TOP_DEFENDERS_COUNT: int = 3

    def __post_init__(self):
        if self.ATTACKER_TICKERS is None:
            self.ATTACKER_TICKERS = ["QQQ", "IEFA", "IEMG", "AGG"]
        if self.DEFENDER_TICKERS is None:
            self.DEFENDER_TICKERS = [
                "BIL",
                "IEF",
                "TLT",
                "LQD",
                "TIP",
                "BND",
                "DBC",
            ]


@dataclass
class LAAConfig:
    """LAA (Lethargic Asset Allocation) 전략 설정"""

    BASE_ALLOCATION: Optional[Dict[str, float]] = None
    SP500_MA_DAYS: int = 200
    UNRATE_MA_MONTHS: int = 12
    QQQ_ALLOCATION: float = 25.0
    SHY_ALLOCATION: float = 25.0

    def __post_init__(self):
        if self.BASE_ALLOCATION is None:
            self.BASE_ALLOCATION = {"VTV": 25, "GLD": 25, "IEF": 25}


@dataclass
class BDAAConfig:
    """BDAA (Bond Dynamic Asset Allocation) 전략 설정"""

    BOND_TICKERS: Optional[List[str]] = None
    TOP_BONDS_COUNT: int = 3
    BOND_ALLOCATION_RATIO: float = 0.0  # __post_init__에서 계산

    def __post_init__(self):
        if self.BOND_TICKERS is None:
            self.BOND_TICKERS = [
                "SHY",
                "IEF",
                "TLT",
                "TIP",
                "LQD",
                "HYG",
                "BWX",
                "EMB",
            ]
        # TOP_BONDS_COUNT가 설정된 후 비율 계산
        self.BOND_ALLOCATION_RATIO = 100.0 / self.TOP_BONDS_COUNT


@dataclass
class MDMConfig:
    """MDM (Modified Dual Momentum) 전략 설정"""

    BOND_TICKERS: Optional[List[str]] = None
    TOP_BONDS_COUNT: int = 3
    BOND_ALLOCATION_RATIO: float = 0.0  # __post_init__에서 계산

    def __post_init__(self):
        if self.BOND_TICKERS is None:
            self.BOND_TICKERS = [
                "SHY",
                "IEF",
                "TLT",
                "TIP",
                "LQD",
                "HYG",
                "BWX",
                "EMB",
            ]
        # TOP_BONDS_COUNT가 설정된 후 비율 계산
        self.BOND_ALLOCATION_RATIO = 100.0 / self.TOP_BONDS_COUNT




@dataclass
class SectorMomentumConfig:
    """Sector Momentum 전략 설정"""

    SECTOR_TICKERS: Optional[List[str]] = None
    DEFENSIVE_TICKER: str = "SGOV"
    TOP_COUNT: int = 2
    MIN_MOMENTUM_SCORE: float = 0.0
    REQUIRE_ABOVE_12M_SMA: bool = True
    BENCHMARK_TICKER: str = "SPY"
    REPLACE_WITH_BENCHMARK_IF_UNDERPERFORMING: bool = True

    def __post_init__(self):
        if self.SECTOR_TICKERS is None:
            self.SECTOR_TICKERS = [
                "XLK",
                "XLC",
                "XLI",
                "XLF",
                "XLE",
                "XLY",
                "XLP",
                "XLV",
                "XLU",
                "XLB",
                "XLRE",
            ]

@dataclass
class APIConfig:
    """API 설정"""

    FRED_API_KEY: str = os.getenv("FRED_API_KEY", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    TWELVEDATA_API_KEY: str = os.getenv("TWELVEDATA_API_KEY", "")
    TWELVEDATA_MAX_CREDITS_PER_MINUTE: int = _get_positive_int_env(
        "TWELVEDATA_MAX_CREDITS_PER_MINUTE", 8
    )
    TWELVEDATA_REQUEST_SLEEP_SECONDS: int = _get_positive_int_env(
        "TWELVEDATA_REQUEST_SLEEP_SECONDS", 65
    )
    FALLBACK_FILE: str = "portfolio.txt"


@dataclass
class PriceProviderConfig:
    """가격 데이터 제공자 설정"""

    PROVIDER: str = os.getenv("PRICE_PROVIDER", "yahoo").lower()


@dataclass
class YFinanceConfig:
    """YFinance 설정"""

    PERIOD: str = "1y"
    INTERVAL: str = "1d"
    AUTO_ADJUST: bool = False
    TIMEOUT: int = 30
    RETRY_COUNT: int = 3


# 전역 설정 인스턴스
TRADING_DAYS = TradingDays()
MOMENTUM_WEIGHTS = MomentumWeights()
STRATEGY_CONFIG = StrategyConfig()
KOREAN_ALL_WEATHER = KoreanAllWeatherConfig()
HAA_CONFIG = HAAConfig()
VAA_CONFIG = VAAConfig()
BAA_CONFIG = BAAConfig()
LAA_CONFIG = LAAConfig()
BDAA_CONFIG = BDAAConfig()
MDM_CONFIG = MDMConfig()
SECTOR_MOMENTUM_CONFIG = SectorMomentumConfig()
API_CONFIG = APIConfig()
YFINANCE_CONFIG = YFinanceConfig()
PRICE_PROVIDER_CONFIG = PriceProviderConfig()


def validate_config() -> bool:
    """설정 유효성을 검증합니다."""
    errors = []

    # 필수 API 키 검증
    if not API_CONFIG.FRED_API_KEY and not os.path.exists(
        API_CONFIG.FALLBACK_FILE
    ):
        errors.append(
            "FRED_API_KEY environment variable or portfolio.txt file required"
        )

    if not API_CONFIG.TELEGRAM_BOT_TOKEN and not os.path.exists(
        API_CONFIG.FALLBACK_FILE
    ):
        errors.append(
            "TELEGRAM_BOT_TOKEN environment variable or "
            "portfolio.txt file required"
        )

    if not API_CONFIG.TELEGRAM_CHAT_ID and not os.path.exists(
        API_CONFIG.FALLBACK_FILE
    ):
        errors.append(
            "TELEGRAM_CHAT_ID environment variable or "
            "portfolio.txt file required"
        )

    # 파일 존재 여부 검증
    if not os.path.exists(STRATEGY_CONFIG.TICKER_FILE):
        errors.append(f"Ticker file not found: {STRATEGY_CONFIG.TICKER_FILE}")

    # 로그 디렉토리 생성
    log_dir = os.path.dirname(STRATEGY_CONFIG.LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    if errors:
        for error in errors:
            print(f"Configuration Error: {error}")
        return False

    return True


def get_momentum_weights_dict() -> Dict[str, int]:
    """모멘텀 가중치를 딕셔너리로 반환합니다."""
    return {
        "12_month": MOMENTUM_WEIGHTS.MONTH_12,
        "6_month": MOMENTUM_WEIGHTS.MONTH_6,
        "3_month": MOMENTUM_WEIGHTS.MONTH_3,
        "1_month": MOMENTUM_WEIGHTS.MONTH_1,
    }


def get_trading_days_dict() -> Dict[str, int]:
    """거래일 상수를 딕셔너리로 반환합니다."""
    return {
        "1_month": TRADING_DAYS.MONTH_1,
        "3_month": TRADING_DAYS.MONTH_3,
        "6_month": TRADING_DAYS.MONTH_6,
        "12_month": TRADING_DAYS.MONTH_12,
    }
