#!/usr/bin/python3
"""Regression tests for main.py scheduled execution flow."""

import importlib
import datetime
import json
import sys
import tempfile
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
    if main_module.SCHEDULED_LATEST_RESULT_PATH == "outputs/latest.json":
        output_root = tempfile.mkdtemp(prefix="scheduled-main-test-")
        monkeypatch.setattr(main_module, "SCHEDULED_OUTPUT_DIR", output_root)
        monkeypatch.setattr(
            main_module,
            "SCHEDULED_HISTORY_DIR",
            f"{output_root}/history",
        )
        monkeypatch.setattr(
            main_module,
            "SCHEDULED_LATEST_RESULT_PATH",
            f"{output_root}/latest.json",
        )

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
    assert info_message_mock.call_args_list[-1].args[0] == "✅ 성공률 100.0% (2/2)"
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
    assert info_message_mock.call_args_list[-1].args[0] == "✅ 성공률 50.0% (1/2)"
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
    assert info_message_mock.call_args_list[-1].args[0] == "✅ 성공률 50.0% (1/2)"
    performance_monitor.log_summary.assert_called_once()


def test_main_exits_when_all_strategies_fail(
    monkeypatch, main_module, tmp_path
):
    """Both strategies fail -> process exits with code 1 and 0% summary."""
    info_message_mock = Mock()
    performance_monitor = Mock()
    snapshot_root = tmp_path / "outputs"
    latest_snapshot = snapshot_root / "latest.json"
    history_snapshot_dir = snapshot_root / "history"

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
    monkeypatch.setattr(main_module, "SCHEDULED_OUTPUT_DIR", str(snapshot_root))
    monkeypatch.setattr(main_module, "SCHEDULED_HISTORY_DIR", str(history_snapshot_dir))
    monkeypatch.setattr(
        main_module, "SCHEDULED_LATEST_RESULT_PATH", str(latest_snapshot)
    )

    with pytest.raises(SystemExit) as exc:
        main_module.main()

    assert exc.value.code == 1
    assert info_message_mock.call_args_list[-1].args[0] == "✅ 성공률 0.0% (0/2)"
    performance_monitor.log_summary.assert_called_once()
    assert not latest_snapshot.exists()
    assert not list(history_snapshot_dir.glob("*.json"))


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
    assert latest_data["status"] == "success"
    assert latest_data["stages"]["strategy_execution"]["status"] == "success"
    assert latest_data["stages"]["snapshot_save"]["status"] == "success"
    assert latest_data["stages"]["notification_reporting"]["status"] in {
        "success",
        "skipped",
    }
    assert latest_data["errors"] == []

    history_files = list(history_dir.glob("*.json"))
    assert len(history_files) == 1
    history_data = json.loads(history_files[0].read_text(encoding="utf-8"))
    assert history_data["strategies"] == latest_data["strategies"]


def test_main_history_snapshot_filename_uses_execution_timezone_clock(
    monkeypatch, main_module, tmp_path
):
    """History snapshot file name is based on shared execution-time helper."""
    output_dir = tmp_path / "outputs"
    history_dir = output_dir / "history"
    latest_path = output_dir / "latest.json"
    fixed_now = datetime.datetime(2026, 4, 1, 8, 30, 0)

    monkeypatch.setattr(main_module, "SCHEDULED_OUTPUT_DIR", str(output_dir))
    monkeypatch.setattr(main_module, "SCHEDULED_HISTORY_DIR", str(history_dir))
    monkeypatch.setattr(
        main_module, "SCHEDULED_LATEST_RESULT_PATH", str(latest_path)
    )
    monkeypatch.setattr(main_module, "get_execution_now", lambda: fixed_now)

    _run_main_with_strategy_results(
        monkeypatch,
        main_module,
        haa_result={"SPY": 50.0},
        kaw_result={"TIGER S&P500": 50.0},
    )

    history_files = list(history_dir.glob("*.json"))
    assert len(history_files) == 1
    assert history_files[0].name == "20260401_083000.json"


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


def test_main_reports_compact_diff_in_info_messages(
    monkeypatch, main_module, tmp_path
):
    """Scheduled run surfaces a compact diff summary in regular message flow."""
    output_dir = tmp_path / "outputs"
    history_dir = output_dir / "history"
    latest_path = output_dir / "latest.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00",
                "strategies": {
                    "HAA": {"SPY": 60.0, "IEF": 40.0},
                    "KAW": {"TIGER S&P500": 100.0},
                },
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

    info_message_mock, _, _, _ = _run_main_with_strategy_results(
        monkeypatch,
        main_module,
        haa_result={"SPY": 50.0, "IEF": 50.0},
        kaw_result={"TIGER S&P500": 100.0},
    )

    emitted_messages = [call.args[0] for call in info_message_mock.call_args_list]
    compact_messages = [
        message
        for message in emitted_messages
        if message.startswith("🔄 변경 사항")
    ]
    assert len(compact_messages) == 1
    assert "1개 전략 변경 / 2개 항목 변경" in compact_messages[0]


def test_main_skips_compact_diff_message_when_no_changes(
    monkeypatch, main_module, tmp_path
):
    """No-change scheduled runs avoid extra diff noise in regular messages."""
    output_dir = tmp_path / "outputs"
    history_dir = output_dir / "history"
    latest_path = output_dir / "latest.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00",
                "strategies": {
                    "HAA": {"SPY": 50.0},
                    "KAW": {"TIGER S&P500": 50.0},
                },
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

    info_message_mock, _, _, _ = _run_main_with_strategy_results(
        monkeypatch,
        main_module,
        haa_result={"SPY": 50.0},
        kaw_result={"TIGER S&P500": 50.0},
    )

    emitted_messages = [call.args[0] for call in info_message_mock.call_args_list]
    assert not any(message.startswith("Scheduled diff:") for message in emitted_messages)


def test_main_continues_when_previous_snapshot_is_malformed_but_loadable(
    monkeypatch, main_module, tmp_path
):
    """Malformed-but-loadable previous snapshot must not fail scheduled run."""
    output_dir = tmp_path / "outputs"
    history_dir = output_dir / "history"
    latest_path = output_dir / "latest.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Loadable JSON with expected shape, but malformed asset value type for diff
    latest_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00",
                "strategies": {"HAA": {"SPY": "not-a-number"}, "KAW": None},
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

    _run_main_with_strategy_results(
        monkeypatch,
        main_module,
        haa_result={"SPY": 100.0},
        kaw_result={"TIGER S&P500": 100.0},
    )

    saved_data = json.loads(latest_path.read_text(encoding="utf-8"))
    assert saved_data["strategies"]["HAA"] == {"SPY": 100.0}
    assert saved_data["strategies"]["KAW"] == {"TIGER S&P500": 100.0}


def test_main_saves_snapshot_even_when_diff_formatting_fails(
    monkeypatch, main_module, tmp_path
):
    """Diff formatting errors should be non-fatal and still save snapshots."""
    output_dir = tmp_path / "outputs"
    history_dir = output_dir / "history"
    latest_path = output_dir / "latest.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00",
                "strategies": {"HAA": {"SPY": 100.0}, "KAW": None},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(main_module, "SCHEDULED_OUTPUT_DIR", str(output_dir))
    monkeypatch.setattr(main_module, "SCHEDULED_HISTORY_DIR", str(history_dir))
    monkeypatch.setattr(
        main_module, "SCHEDULED_LATEST_RESULT_PATH", str(latest_path)
    )
    monkeypatch.setattr(
        main_module,
        "format_execution_diff_summary",
        Mock(side_effect=RuntimeError("diff boom")),
    )

    _run_main_with_strategy_results(
        monkeypatch,
        main_module,
        haa_result={"SPY": 70.0, "QQQ": 30.0},
        kaw_result={"TIGER S&P500": 100.0},
    )

    latest_data = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest_data["strategies"]["HAA"] == {"SPY": 70.0, "QQQ": 30.0}
    assert latest_data["strategies"]["KAW"] == {"TIGER S&P500": 100.0}
    assert latest_data["status"] == "partial_failure"
    assert latest_data["stages"]["notification_reporting"]["status"] == "failure"
    assert latest_data["errors"] == [
        {
            "stage": "notification_reporting",
            "message": "diff boom",
        }
    ]
    assert len(list(history_dir.glob("*.json"))) == 1


def test_print_asset_allocation_emits_grouped_strategy_block(monkeypatch, main_module):
    """Strategy allocation message should be grouped into one readable block."""
    info_message_mock = Mock()
    monkeypatch.setattr(main_module, "print_info_message", info_message_mock)

    main_module.print_asset_allocation(
        {"SPY": 100.0, "QQQ": 50.0},
        {"SPY": "S&P 500", "QQQ": "NASDAQ 100"},
        2,
        "[HAA]",
    )

    info_message_mock.assert_called_once_with(
        "HAA\n- S&P 500 50.00%\n- NASDAQ 100 25.00%"
    )


def test_format_compact_diff_for_telegram_renders_separate_section(main_module):
    compact_summary = (
        "Scheduled diff: 1 strategies changed, 2 allocation entries changed\n"
        "- [~] KAW: KOSEF 200TR -15.00%, KOSEF 국고채10년 +15.00%"
    )

    rendered = main_module.format_compact_diff_for_telegram(compact_summary)

    assert rendered.startswith("🔄 변경 사항\n1개 전략 변경 / 2개 항목 변경")
    assert "- KAW: KOSEF 200TR -15.00%, KOSEF 국고채10년 +15.00%" in rendered


def test_format_compact_diff_for_telegram_no_diff_case_is_clean(main_module):
    rendered = main_module.format_compact_diff_for_telegram("")
    assert rendered == "🔄 변경 사항\n변경 내용 없음"
