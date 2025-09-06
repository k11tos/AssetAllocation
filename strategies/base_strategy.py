#!/usr/bin/python3
"""
Base strategy class for asset allocation strategies
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

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

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        데이터 유효성을 검증합니다.

        Args:
            data: 검증할 데이터

        Returns:
            유효성 여부
        """
        required_keys = self.get_required_data_keys()
        missing_keys = [key for key in required_keys if key not in data]

        if missing_keys:
            self.logger.error(f"Missing required data keys: {missing_keys}")
            return False

        return True

    def execute(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        전략을 실행합니다.

        Args:
            data: 전략에 필요한 데이터

        Returns:
            자산 배분 딕셔너리
        """
        try:
            self.logger.info(f"Starting {self.name} strategy execution...")

            if not self.validate_data(data):
                raise ValueError(f"Invalid data for {self.name} strategy")

            allocation = self.calculate_allocation(data)
            self.logger.info(f"{self.name} strategy executed successfully")

            return allocation

        except Exception as e:
            self.logger.error(f"Error in {self.name} strategy: {str(e)}")
            raise
