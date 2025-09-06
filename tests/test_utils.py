#!/usr/bin/python3
"""
Unit tests for utility classes
"""

import os
import tempfile
import time
import unittest
from pathlib import Path

from utils.cache_manager import CacheManager
from utils.performance_monitor import PerformanceMonitor


class TestCacheManager(unittest.TestCase):
    """CacheManager 테스트"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(
            cache_dir=self.temp_dir, ttl_hours=0.01
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_cache_key(self):
        """캐시 키 생성 테스트"""
        key1 = self.cache_manager._generate_cache_key("SPY QQQ")
        key2 = self.cache_manager._generate_cache_key("SPY QQQ")
        key3 = self.cache_manager._generate_cache_key("QQQ SPY")

        # 같은 입력은 같은 키를 생성해야 함
        self.assertEqual(key1, key2)
        # 다른 입력은 다른 키를 생성해야 함
        self.assertNotEqual(key1, key3)

    def test_cache_set_and_get(self):
        """캐시 저장 및 조회 테스트"""
        test_data = ("test", "data", 123)

        # 데이터 저장
        self.cache_manager.set("SPY", test_data)

        # 데이터 조회
        result = self.cache_manager.get("SPY")
        self.assertEqual(result, test_data)

    def test_cache_expiry(self):
        """캐시 만료 테스트"""
        # 매우 짧은 TTL로 설정 (0.0001시간 = 0.36초)
        short_ttl_cache = CacheManager(
            cache_dir=self.temp_dir, ttl_hours=0.0001
        )

        test_data = ("test", "data")
        short_ttl_cache.set("SPY", test_data)

        # 즉시 조회하면 데이터가 있어야 함
        result = short_ttl_cache.get("SPY")
        self.assertEqual(result, test_data)

        # 충분히 대기 후 조회하면 None이어야 함
        time.sleep(1.0)  # 1초 대기
        result = short_ttl_cache.get("SPY")
        self.assertIsNone(result)

    def test_cache_clear(self):
        """캐시 정리 테스트"""
        # 테스트 데이터 저장
        self.cache_manager.set("SPY", ("data1",))
        self.cache_manager.set("QQQ", ("data2",))

        # 캐시 파일 확인
        cache_files = list(Path(self.temp_dir).glob("*.pkl"))
        self.assertEqual(len(cache_files), 2)

        # 캐시 정리 (모든 파일 삭제)
        cleared_count = self.cache_manager.clear(older_than_hours=0)
        self.assertEqual(cleared_count, 2)

        # 캐시 파일이 삭제되었는지 확인
        cache_files = list(Path(self.temp_dir).glob("*.pkl"))
        self.assertEqual(len(cache_files), 0)

    def test_get_cache_stats(self):
        """캐시 통계 테스트"""
        # 초기 통계
        stats = self.cache_manager.get_cache_stats()
        self.assertEqual(stats["total_files"], 0)
        self.assertEqual(stats["total_size_bytes"], 0)

        # 데이터 저장 후 통계
        self.cache_manager.set("SPY", ("test", "data"))
        stats = self.cache_manager.get_cache_stats()
        self.assertEqual(stats["total_files"], 1)
        self.assertGreater(stats["total_size_bytes"], 0)


class TestPerformanceMonitor(unittest.TestCase):
    """PerformanceMonitor 테스트"""

    def setUp(self):
        self.monitor = PerformanceMonitor()

    def test_time_function_decorator(self):
        """함수 시간 측정 데코레이터 테스트"""

        @self.monitor.time_function("test_func")
        def test_function(delay=0.01):
            time.sleep(delay)
            return "success"

        result = test_function()
        self.assertEqual(result, "success")

        # 메트릭 확인
        metrics = self.monitor.get_metrics()
        self.assertIn("test_func", metrics)
        self.assertEqual(metrics["test_func"]["count"], 1)
        self.assertGreater(metrics["test_func"]["average"], 0.01)

    def test_time_block_context_manager(self):
        """코드 블록 시간 측정 컨텍스트 매니저 테스트"""
        with self.monitor.time_block("test_block"):
            time.sleep(0.01)

        # 메트릭 확인
        metrics = self.monitor.get_metrics()
        self.assertIn("test_block", metrics)
        self.assertEqual(metrics["test_block"]["count"], 1)
        self.assertGreater(metrics["test_block"]["average"], 0.01)

    def test_record_metric(self):
        """메트릭 기록 테스트"""
        self.monitor.record_metric("test_metric", 1.5)
        self.monitor.record_metric("test_metric", 2.5)

        metrics = self.monitor.get_metrics()
        self.assertIn("test_metric", metrics)
        self.assertEqual(metrics["test_metric"]["count"], 2)
        self.assertEqual(metrics["test_metric"]["total"], 4.0)
        self.assertEqual(metrics["test_metric"]["average"], 2.0)
        self.assertEqual(metrics["test_metric"]["min"], 1.5)
        self.assertEqual(metrics["test_metric"]["max"], 2.5)
        self.assertEqual(metrics["test_metric"]["latest"], 2.5)

    def test_reset_metrics(self):
        """메트릭 초기화 테스트"""
        self.monitor.record_metric("test_metric", 1.0)
        self.assertEqual(len(self.monitor.metrics), 1)

        self.monitor.reset_metrics()
        self.assertEqual(len(self.monitor.metrics), 0)

    def test_log_summary(self):
        """로그 요약 테스트"""
        self.monitor.record_metric("test_metric", 1.0)

        # log_summary가 예외 없이 실행되는지 확인
        try:
            self.monitor.log_summary()
        except Exception as e:
            self.fail(f"log_summary raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
