#!/usr/bin/python3
"""
Custom exceptions for asset allocation strategies
"""


class AssetAllocationError(Exception):
    """자산 배분 관련 기본 예외 클래스"""

    def __init__(self, message: str, strategy_name: str = None):
        self.strategy_name = strategy_name
        super().__init__(message)


class DataRetrievalError(AssetAllocationError):
    """데이터 조회 중 발생하는 예외"""

    def __init__(self, message: str, strategy_name: str = None):
        super().__init__(f"Data retrieval failed: {message}", strategy_name)


class DataValidationError(AssetAllocationError):
    """데이터 검증 중 발생하는 예외"""

    def __init__(self, message: str, strategy_name: str = None):
        super().__init__(f"Data validation failed: {message}", strategy_name)


class StrategyExecutionError(AssetAllocationError):
    """전략 실행 중 발생하는 예외"""

    def __init__(self, message: str, strategy_name: str = None):
        super().__init__(
            f"Strategy execution failed: {message}", strategy_name
        )


class NetworkError(AssetAllocationError):
    """네트워크 관련 예외"""

    def __init__(self, message: str, strategy_name: str = None):
        super().__init__(f"Network error: {message}", strategy_name)


class ConfigurationError(AssetAllocationError):
    """설정 관련 예외"""

    def __init__(self, message: str, strategy_name: str = None):
        super().__init__(f"Configuration error: {message}", strategy_name)
