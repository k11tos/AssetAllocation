#!/usr/bin/python3
"""
Tests for config environment parsing.
"""

import pytest

from config import _get_positive_int_env


class TestPositiveIntEnvParsing:
    def test_uses_default_when_env_is_missing(self, monkeypatch):
        monkeypatch.delenv("TWELVEDATA_MAX_CREDITS_PER_MINUTE", raising=False)
        monkeypatch.delenv("TWELVEDATA_REQUEST_SLEEP_SECONDS", raising=False)

        assert _get_positive_int_env("TWELVEDATA_MAX_CREDITS_PER_MINUTE", 8) == 8
        assert _get_positive_int_env("TWELVEDATA_REQUEST_SLEEP_SECONDS", 65) == 65

    def test_uses_valid_override_values(self, monkeypatch):
        monkeypatch.setenv("TWELVEDATA_MAX_CREDITS_PER_MINUTE", "7")
        monkeypatch.setenv("TWELVEDATA_REQUEST_SLEEP_SECONDS", "70")

        assert _get_positive_int_env("TWELVEDATA_MAX_CREDITS_PER_MINUTE", 8) == 7
        assert _get_positive_int_env("TWELVEDATA_REQUEST_SLEEP_SECONDS", 65) == 70

    @pytest.mark.parametrize("bad_value", ["", "abc", "12.3", "1e2"])
    def test_rejects_non_integer_values(self, monkeypatch, bad_value):
        monkeypatch.setenv("TWELVEDATA_MAX_CREDITS_PER_MINUTE", bad_value)

        with pytest.raises(
            ValueError,
            match="TWELVEDATA_MAX_CREDITS_PER_MINUTE must be a positive integer",
        ):
            _get_positive_int_env("TWELVEDATA_MAX_CREDITS_PER_MINUTE", 8)

    @pytest.mark.parametrize("bad_value", ["0", "-1", "-65"])
    def test_rejects_zero_or_negative_values(self, monkeypatch, bad_value):
        monkeypatch.setenv("TWELVEDATA_REQUEST_SLEEP_SECONDS", bad_value)

        with pytest.raises(
            ValueError,
            match="TWELVEDATA_REQUEST_SLEEP_SECONDS must be greater than 0",
        ):
            _get_positive_int_env("TWELVEDATA_REQUEST_SLEEP_SECONDS", 65)
