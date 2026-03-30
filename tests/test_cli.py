#!/usr/bin/python3
"""Regression tests for cli.py strategy selection and output modes."""

import importlib
import json
import re
import sys
import types
from unittest.mock import Mock

import pytest


@pytest.fixture
def cli_module(monkeypatch):
    """Import cli with stubbed dependencies for deterministic/offline tests."""
    config_module = types.ModuleType("config")
    config_module.STRATEGY_CONFIG = types.SimpleNamespace(TICKER_FILE="dummy.json")

    main_module = types.ModuleType("main")
    main_module.main = lambda: None

    portfolio_module = types.ModuleType("portfolio")
    portfolio_module.calculate_rebalancing = lambda *_args, **_kwargs: {}
    portfolio_module.get_baa_allocation = lambda *_args, **_kwargs: {}
    portfolio_module.get_bdaa_allocation = lambda *_args, **_kwargs: {}
    portfolio_module.get_hybrid_asset_allocation = lambda *_args, **_kwargs: {}
    portfolio_module.get_korean_all_weather_allocation = (
        lambda *_args, **_kwargs: {}
    )
    portfolio_module.get_laa_allocation = lambda *_args, **_kwargs: {}
    portfolio_module.get_mdm_allocation = lambda *_args, **_kwargs: {}
    portfolio_module.get_vaa_allocation = lambda *_args, **_kwargs: {}

    data_service_module = types.ModuleType("services.data_service")

    class _DataService:
        def get_financial_data(self, *_args, **_kwargs):
            return ({}, {}, {}, {}, {}, {})

        def get_fred_data(self, *_args, **_kwargs):
            return {}

        def get_cache_stats(self):
            return {
                "total_files": 0,
                "total_size_mb": 0,
                "cache_dir": "./cache",
                "ttl_hours": 24,
            }

        def clear_cache(self):
            return 0

    data_service_module.DataService = _DataService

    cache_module = types.ModuleType("utils.cache_manager")
    cache_module.CacheManager = object

    perf_module = types.ModuleType("utils.performance_monitor")
    perf_module.get_performance_monitor = lambda: Mock()

    optimizer_module = types.ModuleType("utils.strategy_optimizer")
    optimizer_module.get_required_tickers_for_strategy = lambda _name: ["SPY"]
    optimizer_module.print_optimization_summary = lambda: None
    cli_executor_module = types.ModuleType("cli_strategy_executor")
    cli_executor_module.run_haa_strategy = lambda: {"HAA": 100.0}
    cli_executor_module.run_kaw_strategy = lambda: {"KAW": 100.0}
    cli_executor_module.run_baa_strategy = lambda: {"BAA": 100.0}
    cli_executor_module.run_vaa_strategy = lambda: {"VAA": 100.0}
    cli_executor_module.run_laa_strategy = lambda: {"LAA": 100.0}
    cli_executor_module.run_bdaa_strategy = lambda: {"BDAA": 100.0}
    cli_executor_module.run_mdm_strategy = lambda: {"MDM": 100.0}

    monkeypatch.delitem(sys.modules, "cli", raising=False)
    monkeypatch.delitem(sys.modules, "cli_strategy_executor", raising=False)
    monkeypatch.setitem(sys.modules, "config", config_module)
    monkeypatch.setitem(sys.modules, "main", main_module)
    monkeypatch.setitem(sys.modules, "portfolio", portfolio_module)
    monkeypatch.setitem(sys.modules, "services.data_service", data_service_module)
    monkeypatch.setitem(sys.modules, "utils.cache_manager", cache_module)
    monkeypatch.setitem(sys.modules, "utils.performance_monitor", perf_module)
    monkeypatch.setitem(sys.modules, "utils.strategy_optimizer", optimizer_module)
    monkeypatch.setitem(sys.modules, "cli_strategy_executor", cli_executor_module)

    imported_cli_module = importlib.import_module("cli")
    try:
        yield imported_cli_module, cli_executor_module
    finally:
        sys.modules.pop("cli", None)


def _run_cli(monkeypatch, cli_module, args):
    """Run cli.main() with a deterministic argv."""
    monkeypatch.setattr(sys, "argv", ["cli.py", *args])
    cli_module.main()


def test_cli_smoke_all_strategies_json_end_to_end(
    monkeypatch, cli_module, capsys
):
    """Smoke test: run the manual CLI path end-to-end with all strategies in JSON."""
    cli_module, cli_executor_module = cli_module
    expected_allocations = {
        "HAA": {"SPY": 30.0, "IEF": 70.0},
        "KAW": {"KODEX200": 100.0},
        "BAA": {"QQQ": 100.0},
        "VAA": {"BIL": 100.0},
        "LAA": {"IWD": 25.0, "GLD": 25.0, "IEF": 25.0, "QQQ": 25.0},
        "BDAA": {"SPY": 50.0, "TLT": 50.0},
        "MDM": {"SHY": 100.0},
    }

    monkeypatch.setattr(
        cli_executor_module,
        "run_haa_strategy",
        Mock(return_value=expected_allocations["HAA"]),
    )
    monkeypatch.setattr(
        cli_executor_module,
        "run_kaw_strategy",
        Mock(return_value=expected_allocations["KAW"]),
    )
    monkeypatch.setattr(
        cli_executor_module,
        "run_baa_strategy",
        Mock(return_value=expected_allocations["BAA"]),
    )
    monkeypatch.setattr(
        cli_executor_module,
        "run_vaa_strategy",
        Mock(return_value=expected_allocations["VAA"]),
    )
    monkeypatch.setattr(
        cli_executor_module,
        "run_laa_strategy",
        Mock(return_value=expected_allocations["LAA"]),
    )
    monkeypatch.setattr(
        cli_executor_module,
        "run_bdaa_strategy",
        Mock(return_value=expected_allocations["BDAA"]),
    )
    monkeypatch.setattr(
        cli_executor_module,
        "run_mdm_strategy",
        Mock(return_value=expected_allocations["MDM"]),
    )

    _run_cli(monkeypatch, cli_module, ["--strategy", "all", "--output", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert "timestamp" in payload
    assert set(payload["strategies"]) == set(expected_allocations)
    assert payload["strategies"] == expected_allocations


def test_strategy_haa_runs_only_haa(monkeypatch, cli_module, capsys):
    cli_module, cli_executor_module = cli_module
    haa_runner = Mock(return_value={"SPY": 100.0})
    kaw_runner = Mock(return_value={"KAW": 100.0})
    baa_runner = Mock(return_value={"BAA": 100.0})
    vaa_runner = Mock(return_value={"VAA": 100.0})
    laa_runner = Mock(return_value={"LAA": 100.0})
    bdaa_runner = Mock(return_value={"BDAA": 100.0})
    mdm_runner = Mock(return_value={"MDM": 100.0})

    monkeypatch.setattr(cli_executor_module, "run_haa_strategy", haa_runner)
    monkeypatch.setattr(cli_executor_module, "run_kaw_strategy", kaw_runner)
    monkeypatch.setattr(cli_executor_module, "run_baa_strategy", baa_runner)
    monkeypatch.setattr(cli_executor_module, "run_vaa_strategy", vaa_runner)
    monkeypatch.setattr(cli_executor_module, "run_laa_strategy", laa_runner)
    monkeypatch.setattr(cli_executor_module, "run_bdaa_strategy", bdaa_runner)
    monkeypatch.setattr(cli_executor_module, "run_mdm_strategy", mdm_runner)

    _run_cli(monkeypatch, cli_module, ["--strategy", "haa"])

    assert haa_runner.call_count == 1
    assert kaw_runner.call_count == 0
    assert baa_runner.call_count == 0
    assert vaa_runner.call_count == 0
    assert laa_runner.call_count == 0
    assert bdaa_runner.call_count == 0
    assert mdm_runner.call_count == 0
    assert "HAA:" in capsys.readouterr().out


def test_strategy_kaw_runs_only_kaw(monkeypatch, cli_module, capsys):
    cli_module, cli_executor_module = cli_module
    haa_runner = Mock(return_value={"SPY": 100.0})
    kaw_runner = Mock(return_value={"KAW": 100.0})

    monkeypatch.setattr(cli_executor_module, "run_haa_strategy", haa_runner)
    monkeypatch.setattr(cli_executor_module, "run_kaw_strategy", kaw_runner)
    monkeypatch.setattr(cli_executor_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--strategy", "kaw"])

    assert kaw_runner.call_count == 1
    assert haa_runner.call_count == 0
    assert "KAW:" in capsys.readouterr().out


def test_strategy_all_runs_all_supported_strategies(
    monkeypatch, cli_module, capsys
):
    cli_module, cli_executor_module = cli_module
    strategy_mocks = {
        "run_haa_strategy": Mock(return_value={"HAA": 1.0}),
        "run_kaw_strategy": Mock(return_value={"KAW": 1.0}),
        "run_baa_strategy": Mock(return_value={"BAA": 1.0}),
        "run_vaa_strategy": Mock(return_value={"VAA": 1.0}),
        "run_laa_strategy": Mock(return_value={"LAA": 1.0}),
        "run_bdaa_strategy": Mock(return_value={"BDAA": 1.0}),
        "run_mdm_strategy": Mock(return_value={"MDM": 1.0}),
    }

    for attr_name, attr_mock in strategy_mocks.items():
        monkeypatch.setattr(cli_executor_module, attr_name, attr_mock)

    _run_cli(monkeypatch, cli_module, ["--strategy", "all"])

    for attr_mock in strategy_mocks.values():
        assert attr_mock.call_count == 1

    output = capsys.readouterr().out
    for strategy_name in ["HAA", "KAW", "BAA", "VAA", "LAA", "BDAA", "MDM"]:
        assert f"{strategy_name}:" in output


def test_output_text_returns_formatted_text(monkeypatch, cli_module, capsys):
    cli_module, cli_executor_module = cli_module
    monkeypatch.setattr(
        cli_executor_module,
        "run_haa_strategy",
        Mock(return_value={"SPY": 60.0, "IEF": 40.0}),
    )
    monkeypatch.setattr(cli_executor_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--strategy", "haa", "--output", "text"])

    output = capsys.readouterr().out
    assert "Asset Allocation Report" in output
    assert "HAA:" in output
    assert "SPY: 60.00%" in output
    assert "IEF: 40.00%" in output


def test_output_json_returns_valid_json(monkeypatch, cli_module, capsys):
    cli_module, cli_executor_module = cli_module
    monkeypatch.setattr(cli_executor_module, "run_haa_strategy", Mock(return_value={"SPY": 100.0}))
    monkeypatch.setattr(cli_executor_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--strategy", "haa", "--output", "json"])

    parsed = json.loads(capsys.readouterr().out)
    assert "timestamp" in parsed
    assert parsed["strategies"] == {"HAA": {"SPY": 100.0}}


def test_output_csv_returns_expected_headers(monkeypatch, cli_module, capsys):
    cli_module, cli_executor_module = cli_module
    monkeypatch.setattr(cli_executor_module, "run_haa_strategy", Mock(return_value={"SPY": 100.0}))
    monkeypatch.setattr(cli_executor_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--strategy", "haa", "--output", "csv"])

    output = capsys.readouterr().out
    lines = [line for line in output.splitlines() if line.strip()]
    assert lines[0] == "Strategy,Asset,Percentage"
    assert "HAA,SPY,100.00" in lines


def test_save_json_writes_execution_results(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, cli_executor_module = cli_module
    export_path = tmp_path / "outputs" / "latest.json"

    monkeypatch.setattr(
        cli_executor_module, "run_haa_strategy", Mock(return_value={"SPY": 100.0})
    )
    monkeypatch.setattr(cli_executor_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_mdm_strategy", Mock())

    _run_cli(
        monkeypatch,
        cli_module,
        ["--strategy", "haa", "--save-json", str(export_path)],
    )

    output = capsys.readouterr().out
    assert "Asset Allocation Report" in output
    assert export_path.exists()

    with export_path.open("r", encoding="utf-8") as exported_file:
        exported_payload = json.load(exported_file)

    assert "timestamp" in exported_payload
    assert exported_payload["strategies"] == {"HAA": {"SPY": 100.0}}


def test_save_json_not_used_by_default(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, cli_executor_module = cli_module
    default_output_path = tmp_path / "outputs" / "latest.json"

    monkeypatch.setattr(
        cli_executor_module, "run_haa_strategy", Mock(return_value={"SPY": 100.0})
    )
    monkeypatch.setattr(cli_executor_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--strategy", "haa"])

    assert "Asset Allocation Report" in capsys.readouterr().out
    assert not default_output_path.exists()


def test_compare_json_prints_human_readable_diff(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, cli_executor_module = cli_module
    compare_path = tmp_path / "previous.json"
    compare_payload = {
        "timestamp": "2025-01-01T00:00:00",
        "strategies": {
            "HAA": {"SPY": 60.0, "IEF": 40.0},
            "KAW": {"KODEX200": 100.0},
            "OLD": {"CASH": 100.0},
        },
    }
    compare_path.write_text(
        json.dumps(compare_payload, ensure_ascii=False), encoding="utf-8"
    )

    monkeypatch.setattr(
        cli_executor_module,
        "run_haa_strategy",
        Mock(return_value={"SPY": 55.0, "IEF": 35.0, "GLD": 10.0}),
    )
    monkeypatch.setattr(
        cli_executor_module,
        "run_baa_strategy",
        Mock(return_value={"QQQ": 100.0}),
    )
    monkeypatch.setattr(
        cli_executor_module, "run_kaw_strategy", Mock(return_value={"KODEX200": 100.0})
    )
    monkeypatch.setattr(
        cli_executor_module, "run_vaa_strategy", Mock(return_value={"BIL": 100.0})
    )
    monkeypatch.setattr(
        cli_executor_module, "run_laa_strategy", Mock(return_value={"IWD": 100.0})
    )
    monkeypatch.setattr(
        cli_executor_module, "run_bdaa_strategy", Mock(return_value={"SPY": 100.0})
    )
    monkeypatch.setattr(
        cli_executor_module, "run_mdm_strategy", Mock(return_value={"SHY": 100.0})
    )

    _run_cli(
        monkeypatch,
        cli_module,
        ["--strategy", "all", "--compare-json", str(compare_path)],
    )

    output = capsys.readouterr().out
    assert "Asset Allocation Report" in output
    assert "Execution Result Diff" in output
    assert "Added strategies:" in output
    assert "Removed strategies: 1" in output
    assert "- OLD" in output
    assert "HAA:" in output
    assert "* SPY: 60.00% -> 55.00% (-5.00%)" in output
    assert "* IEF: 40.00% -> 35.00% (-5.00%)" in output
    assert "+ Added asset GLD: 10.00%" in output


def test_format_execution_diff_summary_includes_unchanged_counts(cli_module):
    cli_module, _cli_executor_module = cli_module
    previous = {
        "timestamp": "2025-01-01T00:00:00",
        "strategies": {
            "HAA": {"SPY": 50.0, "IEF": 50.0},
            "BAA": {"QQQ": 100.0},
        },
    }
    current = {
        "HAA": {"SPY": 50.0, "IEF": 50.0},
        "BAA": {"QQQ": 90.0, "BIL": 10.0},
        "LAA": {"IWD": 100.0},
    }

    diff = cli_module.format_execution_diff_summary(previous, current)

    assert "Added strategies: 1" in diff
    assert "Changed strategies: 1" in diff
    assert "Unchanged strategies: 1" in diff
    assert "Changed allocation entries: 2" in diff
    assert "Unchanged allocation entries: 2" in diff


def test_format_compact_execution_diff_summary_is_concise(cli_module):
    cli_module, _cli_executor_module = cli_module
    previous = {
        "timestamp": "2025-01-01T00:00:00",
        "strategies": {
            "HAA": {"SPY": 60.0, "IEF": 40.0},
            "KAW": {"TIGER S&P500": 100.0},
        },
    }
    current = {
        "HAA": {"SPY": 50.0, "IEF": 50.0},
        "KAW": {"TIGER S&P500": 100.0},
    }

    summary = cli_module.format_compact_execution_diff_summary(previous, current)

    assert summary is not None
    assert summary.startswith("Scheduled diff:")
    assert "1 strategies changed" in summary
    assert "2 allocation entries changed" in summary


def test_format_compact_execution_diff_summary_returns_none_for_no_changes(cli_module):
    cli_module, _cli_executor_module = cli_module
    previous = {
        "timestamp": "2025-01-01T00:00:00",
        "strategies": {"HAA": {"SPY": 50.0}},
    }
    current = {"HAA": {"SPY": 50.0}}

    summary = cli_module.format_compact_execution_diff_summary(previous, current)

    assert summary is None


def test_format_compact_execution_diff_summary_counts_added_strategy_entries(
    cli_module,
):
    cli_module, _cli_executor_module = cli_module
    previous = {
        "timestamp": "2025-01-01T00:00:00",
        "strategies": {"HAA": {"SPY": 50.0}},
    }
    current = {
        "HAA": {"SPY": 50.0},
        "LAA": {"IWD": 70.0, "GLD": 30.0},
    }

    summary = cli_module.format_compact_execution_diff_summary(previous, current)

    assert summary is not None
    assert "1 strategies changed" in summary
    assert "2 allocation entries changed" in summary


def test_format_compact_execution_diff_summary_counts_removed_strategy_entries(
    cli_module,
):
    cli_module, _cli_executor_module = cli_module
    previous = {
        "timestamp": "2025-01-01T00:00:00",
        "strategies": {
            "HAA": {"SPY": 50.0},
            "KAW": {"TIGER S&P500": 100.0, "KOSEF 200TR": 0.0},
        },
    }
    current = {"HAA": {"SPY": 50.0}}

    summary = cli_module.format_compact_execution_diff_summary(previous, current)

    assert summary is not None
    assert "1 strategies changed" in summary
    assert "2 allocation entries changed" in summary


def test_format_compact_execution_diff_summary_mixed_strategy_and_asset_changes(
    cli_module,
):
    cli_module, _cli_executor_module = cli_module
    previous = {
        "timestamp": "2025-01-01T00:00:00",
        "strategies": {
            "HAA": {"SPY": 60.0, "IEF": 40.0},
            "KAW": {"TIGER S&P500": 100.0},
        },
    }
    current = {
        "HAA": {"SPY": 50.0, "IEF": 50.0},
        "LAA": {"IWD": 100.0},
    }

    summary = cli_module.format_compact_execution_diff_summary(previous, current)

    assert summary is not None
    assert "3 strategies changed" in summary
    assert "4 allocation entries changed" in summary


def test_compare_json_with_json_output_keeps_stdout_valid_json(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, cli_executor_module = cli_module
    compare_path = tmp_path / "previous.json"
    compare_path.write_text(
        json.dumps(
            {
                "timestamp": "2025-01-01T00:00:00",
                "strategies": {"HAA": {"SPY": 60.0, "IEF": 40.0}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cli_executor_module,
        "run_haa_strategy",
        Mock(return_value={"SPY": 55.0, "IEF": 45.0}),
    )
    monkeypatch.setattr(cli_executor_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_mdm_strategy", Mock())

    _run_cli(
        monkeypatch,
        cli_module,
        [
            "--strategy",
            "haa",
            "--output",
            "json",
            "--compare-json",
            str(compare_path),
        ],
    )

    output = capsys.readouterr().out
    parsed = json.loads(output)
    assert parsed["strategies"] == {"HAA": {"SPY": 55.0, "IEF": 45.0}}
    assert "Execution Result Diff" not in output


def test_compare_json_with_csv_output_keeps_stdout_csv_only(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, cli_executor_module = cli_module
    compare_path = tmp_path / "previous.json"
    compare_path.write_text(
        json.dumps(
            {
                "timestamp": "2025-01-01T00:00:00",
                "strategies": {"HAA": {"SPY": 60.0, "IEF": 40.0}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cli_executor_module,
        "run_haa_strategy",
        Mock(return_value={"SPY": 55.0, "IEF": 45.0}),
    )
    monkeypatch.setattr(cli_executor_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_mdm_strategy", Mock())

    _run_cli(
        monkeypatch,
        cli_module,
        [
            "--strategy",
            "haa",
            "--output",
            "csv",
            "--compare-json",
            str(compare_path),
        ],
    )

    output = capsys.readouterr().out
    lines = [line for line in output.splitlines() if line.strip()]
    assert lines[0] == "Strategy,Asset,Percentage"
    assert "HAA,SPY,55.00" in lines
    assert "HAA,IEF,45.00" in lines
    assert "Execution Result Diff" not in output


def test_rebalance_uses_rebalancing_flow(monkeypatch, cli_module, capsys):
    cli_module, cli_executor_module = cli_module
    rebalance_payload = {
        "allocation": {"SPY": 100.0},
        "current_prices": {"SPY": 100.0},
        "current_balances": {"SPY": 1},
    }

    load_rebalance_data = Mock(return_value=rebalance_payload)
    calculate_rebalancing = Mock(
        return_value={
            "SPY": {
                "price": 100.0,
                "current_quantity": 1,
                "current_value": 100.0,
                "current_allocation_pct": 100.0,
                "target_allocation_pct": 100.0,
                "target_value": 100.0,
                "target_quantity": 1,
                "quantity_diff": 0,
                "action": "HOLD",
            }
        }
    )

    haa_runner = Mock(return_value={"SPY": 100.0})

    monkeypatch.setattr(cli_module, "load_rebalance_data", load_rebalance_data)
    monkeypatch.setattr(cli_module, "calculate_rebalancing", calculate_rebalancing)
    monkeypatch.setattr(cli_executor_module, "run_haa_strategy", haa_runner)
    monkeypatch.setattr(cli_executor_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_executor_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--rebalance", "dummy.json"])

    load_rebalance_data.assert_called_once_with("dummy.json")
    calculate_rebalancing.assert_called_once_with(
        {"SPY": 100.0}, {"SPY": 100.0}, {"SPY": 1}
    )
    assert haa_runner.call_count == 0

    output = capsys.readouterr().out
    assert "리밸런싱 리포트" in output
    assert "SPY:" in output


def test_history_lists_recent_snapshots(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, _cli_executor_module = cli_module
    history_dir = tmp_path / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    (history_dir / "20260101_010101.json").write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T01:01:01",
                "strategies": {"HAA": {"SPY": 100.0}},
            }
        ),
        encoding="utf-8",
    )
    (history_dir / "20260102_020202.json").write_text(
        json.dumps(
            {
                "timestamp": "2026-01-02T02:02:02",
                "strategies": {
                    "HAA": {"SPY": 60.0},
                    "KAW": {"TIGER S&P500": 40.0},
                },
            }
        ),
        encoding="utf-8",
    )

    run_selected_mock = Mock()
    monkeypatch.setattr(cli_module, "run_selected_strategies", run_selected_mock)
    monkeypatch.setattr(cli_module, "DEFAULT_HISTORY_DIR", str(history_dir))

    _run_cli(monkeypatch, cli_module, ["--history", "1"])

    output = capsys.readouterr().out
    assert "Execution History (latest 1)" in output
    assert "20260102_020202.json" in output
    assert "strategies=2 [HAA, KAW]" in output
    assert "20260101_010101.json" not in output
    run_selected_mock.assert_not_called()


def test_history_defaults_to_ten_when_count_omitted(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, _cli_executor_module = cli_module
    history_dir = tmp_path / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    for index in range(11):
        file_name = f"202601{index + 1:02d}_000000.json"
        (history_dir / file_name).write_text(
            json.dumps(
                {
                    "timestamp": f"2026-01-{index + 1:02d}T00:00:00",
                    "strategies": {"HAA": {"SPY": 100.0}},
                }
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr(cli_module, "DEFAULT_HISTORY_DIR", str(history_dir))

    _run_cli(monkeypatch, cli_module, ["--history"])

    output = capsys.readouterr().out
    history_lines = [
        line for line in output.splitlines() if re.match(r"^\s*\d+\.\s", line)
    ]
    assert len(history_lines) == 10
    assert "20260111_000000.json" in output
    assert "20260101_000000.json" not in output


def test_history_prints_message_when_directory_has_no_snapshots(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, _cli_executor_module = cli_module
    empty_history_dir = tmp_path / "empty_history"
    empty_history_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(cli_module, "DEFAULT_HISTORY_DIR", str(empty_history_dir))

    _run_cli(monkeypatch, cli_module, ["--history", "3"])

    output = capsys.readouterr().out
    assert "No history snapshots found" in output


def test_history_ignores_invalid_ticker_path(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, _cli_executor_module = cli_module
    history_dir = tmp_path / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    (history_dir / "20260102_020202.json").write_text(
        json.dumps(
            {
                "timestamp": "2026-01-02T02:02:02",
                "strategies": {"HAA": {"SPY": 100.0}},
            }
        ),
        encoding="utf-8",
    )

    run_selected_mock = Mock()
    load_tickers_mock = Mock(side_effect=FileNotFoundError("missing tickers"))
    monkeypatch.setattr(cli_module, "run_selected_strategies", run_selected_mock)
    monkeypatch.setattr(cli_module, "load_tickers", load_tickers_mock)
    monkeypatch.setattr(cli_module, "DEFAULT_HISTORY_DIR", str(history_dir))

    _run_cli(
        monkeypatch,
        cli_module,
        ["--history", "1", "--tickers", "does-not-exist.json"],
    )

    output = capsys.readouterr().out
    assert "Execution History (latest 1)" in output
    assert "20260102_020202.json" in output
    load_tickers_mock.assert_not_called()
    run_selected_mock.assert_not_called()


def test_show_history_displays_snapshot_details_text(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, _cli_executor_module = cli_module
    snapshot_path = tmp_path / "20260102_020202.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-02T02:02:02",
                "strategies": {
                    "HAA": {"SPY": 60.0, "IEF": 40.0},
                    "KAW": {"TIGER S&P500": 100.0},
                },
            }
        ),
        encoding="utf-8",
    )

    run_selected_mock = Mock()
    monkeypatch.setattr(cli_module, "run_selected_strategies", run_selected_mock)

    _run_cli(
        monkeypatch, cli_module, ["--show-history", str(snapshot_path)]
    )

    output = capsys.readouterr().out
    assert "Execution Snapshot Detail" in output
    assert f"File: {snapshot_path}" in output
    assert "Timestamp: 2026-01-02T02:02:02" in output
    assert "Strategy count: 2" in output
    assert "Strategies: HAA, KAW" in output
    assert "[HAA]" in output
    assert "Assets: 2" in output
    assert "- IEF: 40.00%" in output
    assert "- SPY: 60.00%" in output
    assert "[KAW]" in output
    assert "Assets: 1" in output
    assert "- TIGER S&P500: 100.00%" in output
    run_selected_mock.assert_not_called()


def test_show_history_respects_json_output(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, _cli_executor_module = cli_module
    snapshot_path = tmp_path / "20260103_030303.json"
    expected_payload = {
        "timestamp": "2026-01-03T03:03:03",
        "strategies": {"HAA": {"SPY": 100.0}},
    }
    snapshot_path.write_text(
        json.dumps(expected_payload), encoding="utf-8"
    )

    run_selected_mock = Mock()
    monkeypatch.setattr(cli_module, "run_selected_strategies", run_selected_mock)

    _run_cli(
        monkeypatch,
        cli_module,
        ["--show-history", str(snapshot_path), "--output", "json"],
    )

    parsed = json.loads(capsys.readouterr().out)
    assert parsed == expected_payload
    run_selected_mock.assert_not_called()


def test_show_history_handles_invalid_allocation_values_gracefully(
    monkeypatch, cli_module, capsys, tmp_path
):
    cli_module, _cli_executor_module = cli_module
    snapshot_path = tmp_path / "20260104_040404.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-04T04:04:04",
                "strategies": {
                    "HAA": {"SPY": "oops", "IEF": 40.0},
                    "KAW": {"TIGER S&P500": None},
                },
            }
        ),
        encoding="utf-8",
    )

    _run_cli(monkeypatch, cli_module, ["--show-history", str(snapshot_path)])

    output = capsys.readouterr().out
    assert "Execution Snapshot Detail" in output
    assert "Assets: 2" in output
    assert "- IEF: 40.00%" in output
    assert "- SPY: invalid value (oops)" in output
    assert "Assets: 1" in output
    assert "- TIGER S&P500: invalid value (None)" in output
