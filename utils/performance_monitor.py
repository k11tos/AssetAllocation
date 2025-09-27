#!/usr/bin/python3
"""
Performance monitoring utilities
"""

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Optional

LOGGER = logging.getLogger(__name__)


class PerformanceMonitor:
    """성능 모니터링 클래스"""

    def __init__(self):
        self.metrics = {}

    def time_function(self, func_name: str = None):
        """
        함수 실행 시간을 측정하는 데코레이터

        Args:
            func_name: 함수 이름 (기본값: 함수명)
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                name = func_name or func.__name__
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    self.record_metric(name, execution_time)
                    LOGGER.debug(
                        f"{name} executed in {execution_time:.3f} seconds"
                    )

                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    LOGGER.error(
                        f"{name} failed after {execution_time:.3f} seconds: "
                        f"{str(e)}"
                    )
                    raise

            return wrapper

        return decorator

    @contextmanager
    def time_block(self, block_name: str):
        """
        코드 블록의 실행 시간을 측정하는 컨텍스트 매니저

        Args:
            block_name: 블록 이름
        """
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.record_metric(block_name, execution_time)
            LOGGER.debug(
                f"{block_name} executed in {execution_time:.3f} seconds"
            )

    def record_metric(self, name: str, value: float) -> None:
        """
        메트릭을 기록합니다.

        Args:
            name: 메트릭 이름
            value: 메트릭 값
        """
        if name not in self.metrics:
            self.metrics[name] = []

        self.metrics[name].append(value)

    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """기록된 메트릭의 통계를 반환합니다."""
        stats = {}

        for name, values in self.metrics.items():
            if values:
                stats[name] = {
                    "count": len(values),
                    "total": sum(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1],
                }

        return stats

    def reset_metrics(self) -> None:
        """메트릭을 초기화합니다."""
        self.metrics.clear()
        LOGGER.info("Performance metrics reset")

    def log_summary(self) -> None:
        """메트릭 요약을 로그에 출력합니다."""
        stats = self.get_metrics()

        if not stats:
            LOGGER.info("No performance metrics recorded")
            return

        LOGGER.info("=== Performance Summary ===")
        for name, stat in stats.items():
            LOGGER.info(
                f"{name}: "
                f"count={stat['count']}, "
                f"avg={stat['average']:.3f}s, "
                f"min={stat['min']:.3f}s, "
                f"max={stat['max']:.3f}s, "
                f"total={stat['total']:.3f}s"
            )


# 전역 성능 모니터 인스턴스
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """전역 성능 모니터 인스턴스를 반환합니다."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def monitor_performance(func_name: Optional[str] = None):
    """성능 모니터링 데코레이터"""
    monitor = get_performance_monitor()
    return monitor.time_function(func_name)
