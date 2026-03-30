#!/usr/bin/python3
"""Regression tests for main.py scheduled execution flow."""

import importlib
import json
import sys
import types
from unittest.mock import Mock

import pytest

from exceptions import StrategyExecutionError


@pytest.fixture
def main_module(monkeypatch):
    """Load main with test-scoped stub modules for deterministic/offline tests."""
    config_module = types.ModuleType("config")
    config_module.STRATEGY_CONFIG = types.SimpleNamespace(TOTAL_STRATEGIES=2)
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
    portfolio_module.print_info_message = lambda *_args, **_kwargs: None

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

    perf_module = types.ModuleType("utils.performance_monitor")
    perf_module.get_performance_monitor = lambda: Mock()
    optimizer_module = types.ModuleType("utils.strategy_optimizer")
    optimizer_module.get_required_tickers_for_strategy = lambda _name: ["SPY"]

    monkeypatch.delitem(sys.modules, "main", raising=False)
    monkeypatch.setitem(sys.modules, "config", config_module)
    monkeypatch.setitem(sys.modules, "portfolio", portfolio_module)
    monkeypatch.setitem(
        sys.modules,
        "utils.logging_config",
        logging_config_module,
    )
    monkeypatch.setitem(sys.modules, "utils.performance_monitor", perf_module)
    monkeypatch.setitem(sys.modules, "utils.strategy_optimizer", optimizer_module)
    return importlib.import_module("main")


def _run_main_with_strategy_results(monkeypatch, main_module, haa_result, kaw_result):
    """Run main.main() with deterministic strategy outcomes and return mocks."""
    info_message_mock = Mock()
    print_allocation_mock = Mock()
    performance_monitor = Mock()

    monkeypatch.setattr(main_module, "validate_config", lambda: True)
    monkeypatch.setattr(main_module, "load_tickers", lambda: ["SPY", "QQQ"])
    monkeypatch.setattr(main_module, "print_info_message", info_message_mock)
    monkeypatch.setattr(
        main_module,
        "print_asset_allocation",
        print_allocation_mock,
    )
    monkeypatch.setattr(
        main_module,
        "get_performance_monitor",
        lambda: performance_monitor,
    )
    run_selected_mock = Mock(wraps=main_module.run_selected_strategies)
    monkeypatch.setattr(main_module, "run_selected_strategies", run_selected_mock)

    monkeypatch.setattr(
        main_module,
        "execute_haa_strategy",
        Mock(side_effect=haa_result)
        if isinstance(haa_result, Exception)
        else Mock(return_value=haa_result),
    )
    monkeypatch.setattr(
        main_module,
        "execute_kaw_strategy",
        Mock(side_effect=kaw_result)
        if isinstance(kaw_result, Exception)
        else Mock(return_value=kaw_result),
    )

    main_module.main()
    return (
        info_message_mock,
        print_allocation_mock,
        performance_monitor,
        run_selected_mock,
    )


def test_main_exits_when_validate_config_fails(monkeypatch, main_module):
    """validate_config() is False -> process exits with code 1."""
    performance_monitor = Mock()
    monkeypatch.setattr(main_module, "validate_config", lambda: False)
    monkeypatch.setattr(
        main_module,
        "get_performance_monitor",
        lambda: performance_monitor,
    )

    with pytest.raises(SystemExit) as exc:
        main_module.main()

    assert exc.value.code == 1
    performance_monitor.log_summary.assert_not_called()


def test_main_succeeds_when_haa_and_kaw_succeed(monkeypatch, main_module):
    """Both strategies succeed -> normal completion and 100% summary."""
    info_message_mock, print_allocation_mock, performance_monitor, run_selected_mock = (
        _run_main_with_strategy_results(
            monkeypatch,
            main_module,
            haa_result={"SPY": 50.0},
            kaw_result={"TIGER S&P500": 50.0},
        )
    )

    assert print_allocation_mock.call_count == 2
    run_selected_mock.assert_called_once_with(["HAA", "KAW"], "main")
    assert info_message_mock.call_args_list[-1].args[0] == "성공률: 100.0% (2/2)"
    performance_monitor.log_summary.assert_called_once()


def test_main_continues_when_haa_fails_and_kaw_succeeds(monkeypatch, main_module):
    """HAA fails and KAW succeeds -> process continues and succeeds overall."""
    info_message_mock, print_allocation_mock, performance_monitor, _ = (
        _run_main_with_strategy_results(
            monkeypatch,
            main_module,
            haa_result=None,
            kaw_result={"TIGER S&P500": 100.0},
        )
    )

    assert print_allocation_mock.call_count == 1
    assert info_message_mock.call_args_list[-1].args[0] == "성공률: 50.0% (1/2)"
    performance_monitor.log_summary.assert_called_once()


def test_main_continues_when_haa_succeeds_and_kaw_fails(monkeypatch, main_module):
    """HAA succeeds and KAW fails -> process continues and succeeds overall."""
    info_message_mock, print_allocation_mock, performance_monitor, _ = (
        _run_main_with_strategy_results(
            monkeypatch,
            main_module,
            haa_result={"SPY": 100.0},
            kaw_result=StrategyExecutionError("kaw failed"),
        )
    )

    assert print_allocation_mock.call_count == 1
    assert info_message_mock.call_args_list[-1].args[0] == "성공률: 50.0% (1/2)"
    performance_monitor.log_summary.assert_called_once()


def test_main_exits_when_all_strategies_fail(monkeypatch, main_module):
    """Both strategies fail -> process exits with code 1 and 0% summary."""
    info_message_mock = Mock()
    performance_monitor = Mock()

    monkeypatch.setattr(main_module, "validate_config", lambda: True)
    monkeypatch.setattr(main_module, "load_tickers", lambda: ["SPY"])
    monkeypatch.setattr(main_module, "print_info_message", info_message_mock)
    monkeypatch.setattr(main_module, "print_asset_allocation", Mock())
    monkeypatch.setattr(main_module, "execute_haa_strategy", Mock(return_value=None))
    monkeypatch.setattr(main_module, "execute_kaw_strategy", Mock(return_value=None))
    monkeypatch.setattr(
        main_module,
        "get_performance_monitor",
        lambda: performance_monitor,
    )

    with pytest.raises(SystemExit) as exc:
        main_module.main()

    assert exc.value.code == 1
    assert info_message_mock.call_args_list[-1].args[0] == "성공률: 0.0% (0/2)"
    performance_monitor.log_summary.assert_called_once()


def test_main_saves_latest_and_history_results(
    monkeypatch, main_module, tmp_path
):
    """Successful scheduled run persists latest and timestamped history JSON."""
    output_dir = tmp_path / "outputs"
    history_dir = output_dir / "history"
    latest_path = output_dir / "latest.json"

    monkeypatch.setattr(main_module, "SCHEDULED_OUTPUT_DIR", str(output_dir))
    monkeypatch.setattr(main_module, "SCHEDULED_HISTORY_DIR", str(history_dir))
    monkeypatch.setattr(
        main_module, "SCHEDULED_LATEST_RESULT_PATH", str(latest_path)
    )

    _run_main_with_strategy_results(
        monkeypatch,
        main_module,
        haa_result={"SPY": 50.0},
        kaw_result={"TIGER S&P500": 50.0},
    )

    assert latest_path.exists()
    latest_data = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest_data["strategies"]["HAA"] == {"SPY": 50.0}
    assert latest_data["strategies"]["KAW"] == {"TIGER S&P500": 50.0}

    history_files = list(history_dir.glob("*.json"))
    assert len(history_files) == 1
    history_data = json.loads(history_files[0].read_text(encoding="utf-8"))
    assert history_data["strategies"] == latest_data["strategies"]


def test_main_logs_diff_when_previous_snapshot_exists(
    monkeypatch, main_module, tmp_path
):
    """When latest snapshot exists, scheduled run logs a diff summary."""
    output_dir = tmp_path / "outputs"
    history_dir = output_dir / "history"
    latest_path = output_dir / "latest.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    latest_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00",
                "strategies": {"HAA": {"SPY": 100.0}, "KAW": None},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(main_module, "SCHEDULED_OUTPUT_DIR", str(output_dir))
    monkeypatch.setattr(main_module, "SCHEDULED_HISTORY_DIR", str(history_dir))
    monkeypatch.setattr(
        main_module, "SCHEDULED_LATEST_RESULT_PATH", str(latest_path)
    )
    monkeypatch.setattr(main_module.LOGGER, "info", Mock())

    _run_main_with_strategy_results(
        monkeypatch,
        main_module,
        haa_result={"SPY": 50.0, "QQQ": 50.0},
        kaw_result={"TIGER S&P500": 100.0},
    )

    logger_messages = [
        call.args[0]
        for call in main_module.LOGGER.info.call_args_list
        if call.args
    ]
    assert any(
        "Scheduled execution diff summary" in message
        for message in logger_messages
    )
