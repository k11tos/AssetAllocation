#!/usr/bin/python3
"""Regression tests for main.py scheduled execution flow."""

import sys
import types
from unittest.mock import Mock

import pytest

# Lightweight stubs for main.py imports so tests stay offline and deterministic.
if "config" not in sys.modules:
    config_module = types.ModuleType("config")
    config_module.STRATEGY_CONFIG = types.SimpleNamespace(TOTAL_STRATEGIES=2)
    config_module.validate_config = lambda: True
    sys.modules["config"] = config_module

if "portfolio" not in sys.modules:
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
    portfolio_module.print_info_message = lambda *_args, **_kwargs: None
    sys.modules["portfolio"] = portfolio_module

if "utils.logging_config" not in sys.modules:
    logging_config_module = types.ModuleType("utils.logging_config")

    class _LoggingConfig:
        @staticmethod
        def get_logger(_name):
            return Mock()

        @staticmethod
        def log_strategy_start(*_args, **_kwargs):
            return None

        @staticmethod
        def log_strategy_success(*_args, **_kwargs):
            return None

        @staticmethod
        def log_allocation_result(*_args, **_kwargs):
            return None

        @staticmethod
        def log_strategy_failure(*_args, **_kwargs):
            return None

        @staticmethod
        def log_error_with_context(*_args, **_kwargs):
            return None

    logging_config_module.LoggingConfig = _LoggingConfig
    sys.modules["utils.logging_config"] = logging_config_module

if "utils.performance_monitor" not in sys.modules:
    perf_module = types.ModuleType("utils.performance_monitor")
    perf_module.get_performance_monitor = lambda: Mock()
    sys.modules["utils.performance_monitor"] = perf_module

if "utils.strategy_optimizer" not in sys.modules:
    optimizer_module = types.ModuleType("utils.strategy_optimizer")
    optimizer_module.get_required_tickers_for_strategy = lambda _name: ["SPY"]
    sys.modules["utils.strategy_optimizer"] = optimizer_module

import main
from exceptions import StrategyExecutionError


def _run_main_with_strategy_results(monkeypatch, haa_result, kaw_result):
    """Run main.main() with deterministic strategy outcomes and return mocks."""
    info_message_mock = Mock()
    print_allocation_mock = Mock()
    performance_monitor = Mock()

    monkeypatch.setattr(main, "validate_config", lambda: True)
    monkeypatch.setattr(main, "load_tickers", lambda: ["SPY", "QQQ"])
    monkeypatch.setattr(main, "print_info_message", info_message_mock)
    monkeypatch.setattr(main, "print_asset_allocation", print_allocation_mock)
    monkeypatch.setattr(
        main,
        "get_performance_monitor",
        lambda: performance_monitor,
    )

    if isinstance(haa_result, Exception):
        monkeypatch.setattr(
            main,
            "execute_haa_strategy",
            Mock(side_effect=haa_result),
        )
    else:
        monkeypatch.setattr(main, "execute_haa_strategy", lambda: haa_result)

    if isinstance(kaw_result, Exception):
        monkeypatch.setattr(
            main,
            "get_korean_all_weather_allocation",
            Mock(side_effect=kaw_result),
        )
    else:
        monkeypatch.setattr(
            main,
            "get_korean_all_weather_allocation",
            lambda: kaw_result,
        )

    main.main()
    return info_message_mock, print_allocation_mock, performance_monitor


def test_main_exits_when_validate_config_fails(monkeypatch):
    """validate_config() is False -> process exits with code 1."""
    performance_monitor = Mock()
    monkeypatch.setattr(main, "validate_config", lambda: False)
    monkeypatch.setattr(main, "get_performance_monitor", lambda: performance_monitor)

    with pytest.raises(SystemExit) as exc:
        main.main()

    assert exc.value.code == 1
    performance_monitor.log_summary.assert_not_called()


def test_main_succeeds_when_haa_and_kaw_succeed(monkeypatch):
    """Both strategies succeed -> normal completion and 100% summary."""
    info_message_mock, print_allocation_mock, performance_monitor = (
        _run_main_with_strategy_results(
            monkeypatch,
            haa_result={"SPY": 50.0},
            kaw_result={"TIGER S&P500": 50.0},
        )
    )

    assert print_allocation_mock.call_count == 2
    assert info_message_mock.call_args_list[-1].args[0] == "성공률: 100.0% (2/2)"
    performance_monitor.log_summary.assert_called_once()


def test_main_continues_when_haa_fails_and_kaw_succeeds(monkeypatch):
    """HAA fails and KAW succeeds -> process continues and succeeds overall."""
    info_message_mock, print_allocation_mock, performance_monitor = (
        _run_main_with_strategy_results(
            monkeypatch,
            haa_result=None,
            kaw_result={"TIGER S&P500": 100.0},
        )
    )

    assert print_allocation_mock.call_count == 1
    assert info_message_mock.call_args_list[-1].args[0] == "성공률: 50.0% (1/2)"
    performance_monitor.log_summary.assert_called_once()


def test_main_continues_when_haa_succeeds_and_kaw_fails(monkeypatch):
    """HAA succeeds and KAW fails -> process continues and succeeds overall."""
    info_message_mock, print_allocation_mock, performance_monitor = (
        _run_main_with_strategy_results(
            monkeypatch,
            haa_result={"SPY": 100.0},
            kaw_result=StrategyExecutionError("kaw failed"),
        )
    )

    assert print_allocation_mock.call_count == 1
    assert info_message_mock.call_args_list[-1].args[0] == "성공률: 50.0% (1/2)"
    performance_monitor.log_summary.assert_called_once()


def test_main_exits_when_all_strategies_fail(monkeypatch):
    """Both strategies fail -> process exits with code 1 and 0% summary."""
    info_message_mock = Mock()
    performance_monitor = Mock()

    monkeypatch.setattr(main, "validate_config", lambda: True)
    monkeypatch.setattr(main, "load_tickers", lambda: ["SPY"])
    monkeypatch.setattr(main, "print_info_message", info_message_mock)
    monkeypatch.setattr(main, "print_asset_allocation", Mock())
    monkeypatch.setattr(main, "execute_haa_strategy", lambda: None)
    monkeypatch.setattr(
        main,
        "get_korean_all_weather_allocation",
        Mock(side_effect=StrategyExecutionError("kaw failed")),
    )
    monkeypatch.setattr(main, "get_performance_monitor", lambda: performance_monitor)

    with pytest.raises(SystemExit) as exc:
        main.main()

    assert exc.value.code == 1
    assert info_message_mock.call_args_list[-1].args[0] == "성공률: 0.0% (0/2)"
    performance_monitor.log_summary.assert_called_once()
