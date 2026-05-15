#!/usr/bin/python3
"""Offline smoke test for main.py scheduled execution path."""

import datetime
import importlib
import sys
import types
from unittest.mock import Mock

import pytest


@pytest.fixture
def main_module(monkeypatch):
    """Load main with offline-safe stub modules for deterministic smoke testing."""
    config_module = types.ModuleType("config")
    config_module.STRATEGY_CONFIG = types.SimpleNamespace(TICKER_FILE="unused.json")
    config_module.SCHEDULED_STRATEGIES = ["HAA", "KAW", "SECTOR_MOMENTUM"]
    config_module.SCHEDULED_STRATEGY_WEIGHTS = {"HAA": 45.0, "KAW": 45.0, "SECTOR_MOMENTUM": 10.0}
    config_module.validate_config = lambda: True

    portfolio_module = types.ModuleType("portfolio")
    portfolio_module.get_financial_data = lambda *_args, **_kwargs: (
        {},
        {},
        {},
        {},
        {},
        {},
    )
    portfolio_module.get_hybrid_asset_allocation = lambda *_args, **_kwargs: {}
    portfolio_module.get_korean_all_weather_allocation = (
        lambda *_args, **_kwargs: {}
    )
    portfolio_module.get_sector_momentum_allocation = lambda *_args, **_kwargs: {}
    portfolio_module.print_info_message = lambda *_args, **_kwargs: None

    strategy_runner_module = types.ModuleType("strategy_runner")
    strategy_runner_module.run_selected_strategies = lambda *_args, **_kwargs: {
        "HAA": {},
        "KAW": {},
    }

    logging_config_module = types.ModuleType("utils.logging_config")

    class _LoggingConfig:
        @staticmethod
        def get_logger(_name):
            return Mock()

        @staticmethod
        def log_error_with_context(*_args, **_kwargs):
            return None

    logging_config_module.LoggingConfig = _LoggingConfig

    perf_module = types.ModuleType("utils.performance_monitor")
    perf_module.get_performance_monitor = lambda: Mock()

    optimizer_module = types.ModuleType("utils.strategy_optimizer")
    optimizer_module.get_required_tickers_for_strategy = lambda _name: ["SPY"]

    monkeypatch.delitem(sys.modules, "main", raising=False)
    monkeypatch.setitem(sys.modules, "config", config_module)
    monkeypatch.setitem(sys.modules, "portfolio", portfolio_module)
    monkeypatch.setitem(sys.modules, "strategy_runner", strategy_runner_module)
    monkeypatch.setitem(
        sys.modules,
        "utils.logging_config",
        logging_config_module,
    )
    monkeypatch.setitem(sys.modules, "utils.performance_monitor", perf_module)
    monkeypatch.setitem(sys.modules, "utils.strategy_optimizer", optimizer_module)

    return importlib.import_module("main")


def test_main_scheduled_smoke_success_offline(monkeypatch, main_module):
    """Scheduled main flow runs end-to-end with deterministic mocked services."""
    info_message_mock = Mock()
    performance_monitor = Mock()

    monkeypatch.setattr(main_module, "validate_config", Mock(return_value=True))
    monkeypatch.setattr(main_module, "load_tickers", Mock(return_value=["SPY", "QQQ"]))
    monkeypatch.setattr(
        main_module,
        "run_selected_strategies",
        Mock(
            return_value={
                "HAA": {"SPY": 60.0, "QQQ": 40.0},
                "KAW": {"TIGER S&P500": 100.0},
                "SECTOR_MOMENTUM": {"XLK": 100.0},
            }
        ),
    )
    monkeypatch.setattr(main_module, "print_info_message", info_message_mock)
    monkeypatch.setattr(
        main_module,
        "get_performance_monitor",
        Mock(return_value=performance_monitor),
    )
    monkeypatch.setattr(
        main_module,
        "get_execution_now",
        Mock(return_value=datetime.datetime(2026, 1, 15, 9, 30, 0)),
    )

    main_module.main()

    main_module.validate_config.assert_called_once_with()
    main_module.load_tickers.assert_called_once_with()
    main_module.run_selected_strategies.assert_called_once_with(["HAA", "KAW", "SECTOR_MOMENTUM"], "main")

    assert info_message_mock.call_count == 1
    rendered_report = info_message_mock.call_args_list[0].args[0]
    assert rendered_report.startswith("📊 자산 배분 리포트 | 2026-01-15 (Thu)")
    assert "✅ 성공률 100.0% (3/3)" in rendered_report
    assert "\n\n[HAA]\n- SPY 27.00%\n- QQQ 18.00%" in rendered_report
    assert "\n\n[KAW]\n- TIGER S&P500 45.00%" in rendered_report
    assert "\n\n[SECTOR_MOMENTUM]\n- XLK 10.00%" in rendered_report

    performance_monitor.log_summary.assert_called_once_with()
