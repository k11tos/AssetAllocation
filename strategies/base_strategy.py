#!/usr/bin/python3
"""
Base strategy class for asset allocation strategies
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from exceptions import DataValidationError, StrategyExecutionError

LOGGER = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """기본 전략 클래스"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        자산 배분을 계산합니다.

        Args:
            data: 전략에 필요한 데이터

        Returns:
            자산 배분 딕셔너리 (티커: 비율)
        """
        pass

    @abstractmethod
    def get_required_data_keys(self) -> list:
        """
        전략 실행에 필요한 데이터 키 목록을 반환합니다.

        Returns:
            필요한 데이터 키 목록
        """
        pass

    def validate_data(self, data: Dict[str, Any]) -> None:
        """
        데이터 유효성을 검증합니다.

        Args:
            data: 검증할 데이터

        Raises:
            DataValidationError: 데이터 검증 실패 시
        """
        required_keys = self.get_required_data_keys()
        missing_keys = [key for key in required_keys if key not in data]

        if missing_keys:
            error_msg = f"Missing required data keys: {missing_keys}"
            self.logger.error(error_msg)
            raise DataValidationError(error_msg, self.name)

    def execute(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        전략을 실행합니다.

        Args:
            data: 전략에 필요한 데이터

        Returns:
            자산 배분 딕셔너리

        Raises:
            DataValidationError: 데이터 검증 실패 시
            StrategyExecutionError: 전략 실행 실패 시
        """
        try:
            self.logger.info(f"Starting {self.name} strategy execution...")

            # 데이터 검증 (예외 발생 가능)
            self.validate_data(data)

            # 전략 실행
            allocation = self.calculate_allocation(data)

            # 결과 검증
            if not allocation or not isinstance(allocation, dict):
                raise StrategyExecutionError(
                    "Strategy returned invalid allocation result", self.name
                )

            # 배분 합계 검증 (100%에 가까운지 확인)
            total_allocation = sum(allocation.values())
            if abs(total_allocation - 100.0) > 0.01:  # 0.01% 허용 오차
                self.logger.warning(
                    f"Total allocation is {total_allocation:.2f}%, not 100%"
                )

            self.logger.info(f"{self.name} strategy executed successfully")
            return allocation

        except (DataValidationError, StrategyExecutionError):
            # 이미 정의된 예외는 그대로 전파
            raise
        except Exception as e:
            # 예상치 못한 예외는 StrategyExecutionError로 래핑
            error_msg = f"Unexpected error during strategy execution: {str(e)}"
            self.logger.error(error_msg)
            raise StrategyExecutionError(error_msg, self.name) from e
