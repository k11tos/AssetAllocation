#!/usr/bin/python3
"""
Cache management for financial data
"""

import hashlib
import json
import logging
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class CacheManager:
    """금융 데이터 캐시 관리자"""

    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 1):
        """
        캐시 관리자를 초기화합니다.

        Args:
            cache_dir: 캐시 디렉토리 경로
            ttl_hours: 캐시 유효 시간 (시간)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

        LOGGER.info(f"Cache manager initialized with TTL: {ttl_hours} hours")

    def _generate_cache_key(self, tickers: str, **kwargs) -> str:
        """
        캐시 키를 생성합니다.

        Args:
            tickers: 티커 문자열
            **kwargs: 추가 파라미터

        Returns:
            캐시 키 해시
        """
        key_data = {"tickers": tickers, **kwargs}
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """캐시 파일 경로를 반환합니다."""
        return self.cache_dir / f"{cache_key}.pkl"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """캐시가 유효한지 확인합니다."""
        if not cache_path.exists():
            return False

        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - file_time < self.ttl

    def get(self, tickers: str, **kwargs) -> Optional[Tuple]:
        """
        캐시에서 데이터를 가져옵니다.

        Args:
            tickers: 티커 문자열
            **kwargs: 추가 파라미터

        Returns:
            캐시된 데이터 또는 None
        """
        cache_key = self._generate_cache_key(tickers, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        if not self._is_cache_valid(cache_path):
            LOGGER.debug(f"Cache miss or expired for key: {cache_key}")
            return None

        try:
            with open(cache_path, "rb") as f:
                data = pickle.load(f)
            LOGGER.debug(f"Cache hit for key: {cache_key}")
            return data
        except Exception as e:
            LOGGER.warning(f"Failed to load cache: {str(e)}")
            return None

    def set(self, tickers: str, data: Tuple, **kwargs) -> None:
        """
        데이터를 캐시에 저장합니다.

        Args:
            tickers: 티커 문자열
            data: 저장할 데이터
            **kwargs: 추가 파라미터
        """
        cache_key = self._generate_cache_key(tickers, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(data, f)
            LOGGER.debug(f"Data cached with key: {cache_key}")
        except Exception as e:
            LOGGER.warning(f"Failed to save cache: {str(e)}")

    def clear(self, older_than_hours: int = 24) -> int:
        """
        오래된 캐시 파일들을 삭제합니다.

        Args:
            older_than_hours: 삭제할 캐시의 최소 나이 (시간)

        Returns:
            삭제된 파일 수
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        deleted_count = 0

        for cache_file in self.cache_dir.glob("*.pkl"):
            if (
                datetime.fromtimestamp(cache_file.stat().st_mtime)
                < cutoff_time
            ):
                try:
                    cache_file.unlink()
                    deleted_count += 1
                    LOGGER.debug(f"Deleted old cache file: {cache_file}")
                except Exception as e:
                    LOGGER.warning(
                        f"Failed to delete cache file {cache_file}: {str(e)}"
                    )

        LOGGER.info(f"Cleared {deleted_count} old cache files")
        return deleted_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계를 반환합니다."""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "total_files": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.ttl.total_seconds() / 3600,
        }
