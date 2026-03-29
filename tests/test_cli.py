#!/usr/bin/python3
"""Regression tests for cli.py strategy selection and output modes."""

import importlib
import json
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

    monkeypatch.delitem(sys.modules, "cli", raising=False)
    monkeypatch.setitem(sys.modules, "config", config_module)
    monkeypatch.setitem(sys.modules, "main", main_module)
    monkeypatch.setitem(sys.modules, "portfolio", portfolio_module)
    monkeypatch.setitem(sys.modules, "services.data_service", data_service_module)
    monkeypatch.setitem(sys.modules, "utils.cache_manager", cache_module)
    monkeypatch.setitem(sys.modules, "utils.performance_monitor", perf_module)
    monkeypatch.setitem(sys.modules, "utils.strategy_optimizer", optimizer_module)

    return importlib.import_module("cli")


def _run_cli(monkeypatch, cli_module, args):
    """Run cli.main() with a deterministic argv."""
    monkeypatch.setattr(sys, "argv", ["cli.py", *args])
    cli_module.main()


def test_strategy_haa_runs_only_haa(monkeypatch, cli_module, capsys):
    haa_runner = Mock(return_value={"SPY": 100.0})
    kaw_runner = Mock(return_value={"KAW": 100.0})
    baa_runner = Mock(return_value={"BAA": 100.0})
    vaa_runner = Mock(return_value={"VAA": 100.0})
    laa_runner = Mock(return_value={"LAA": 100.0})
    bdaa_runner = Mock(return_value={"BDAA": 100.0})
    mdm_runner = Mock(return_value={"MDM": 100.0})

    monkeypatch.setattr(cli_module, "run_haa_strategy", haa_runner)
    monkeypatch.setattr(cli_module, "run_kaw_strategy", kaw_runner)
    monkeypatch.setattr(cli_module, "run_baa_strategy", baa_runner)
    monkeypatch.setattr(cli_module, "run_vaa_strategy", vaa_runner)
    monkeypatch.setattr(cli_module, "run_laa_strategy", laa_runner)
    monkeypatch.setattr(cli_module, "run_bdaa_strategy", bdaa_runner)
    monkeypatch.setattr(cli_module, "run_mdm_strategy", mdm_runner)

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
    haa_runner = Mock(return_value={"SPY": 100.0})
    kaw_runner = Mock(return_value={"KAW": 100.0})

    monkeypatch.setattr(cli_module, "run_haa_strategy", haa_runner)
    monkeypatch.setattr(cli_module, "run_kaw_strategy", kaw_runner)
    monkeypatch.setattr(cli_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--strategy", "kaw"])

    assert kaw_runner.call_count == 1
    assert haa_runner.call_count == 0
    assert "KAW:" in capsys.readouterr().out


def test_strategy_all_runs_all_supported_strategies(
    monkeypatch, cli_module, capsys
):
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
        monkeypatch.setattr(cli_module, attr_name, attr_mock)

    _run_cli(monkeypatch, cli_module, ["--strategy", "all"])

    for attr_mock in strategy_mocks.values():
        assert attr_mock.call_count == 1

    output = capsys.readouterr().out
    for strategy_name in ["HAA", "KAW", "BAA", "VAA", "LAA", "BDAA", "MDM"]:
        assert f"{strategy_name}:" in output


def test_output_text_returns_formatted_text(monkeypatch, cli_module, capsys):
    monkeypatch.setattr(
        cli_module,
        "run_haa_strategy",
        Mock(return_value={"SPY": 60.0, "IEF": 40.0}),
    )
    monkeypatch.setattr(cli_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--strategy", "haa", "--output", "text"])

    output = capsys.readouterr().out
    assert "Asset Allocation Report" in output
    assert "HAA:" in output
    assert "SPY: 60.00%" in output
    assert "IEF: 40.00%" in output


def test_output_json_returns_valid_json(monkeypatch, cli_module, capsys):
    monkeypatch.setattr(cli_module, "run_haa_strategy", Mock(return_value={"SPY": 100.0}))
    monkeypatch.setattr(cli_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--strategy", "haa", "--output", "json"])

    parsed = json.loads(capsys.readouterr().out)
    assert "timestamp" in parsed
    assert parsed["strategies"] == {"HAA": {"SPY": 100.0}}


def test_output_csv_returns_expected_headers(monkeypatch, cli_module, capsys):
    monkeypatch.setattr(cli_module, "run_haa_strategy", Mock(return_value={"SPY": 100.0}))
    monkeypatch.setattr(cli_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--strategy", "haa", "--output", "csv"])

    output = capsys.readouterr().out
    lines = [line for line in output.splitlines() if line.strip()]
    assert lines[0] == "Strategy,Asset,Percentage"
    assert "HAA,SPY,100.00" in lines


def test_rebalance_uses_rebalancing_flow(monkeypatch, cli_module, capsys):
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
    monkeypatch.setattr(cli_module, "run_haa_strategy", haa_runner)
    monkeypatch.setattr(cli_module, "run_kaw_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_baa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_vaa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_laa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_bdaa_strategy", Mock())
    monkeypatch.setattr(cli_module, "run_mdm_strategy", Mock())

    _run_cli(monkeypatch, cli_module, ["--rebalance", "dummy.json"])

    load_rebalance_data.assert_called_once_with("dummy.json")
    calculate_rebalancing.assert_called_once_with(
        {"SPY": 100.0}, {"SPY": 100.0}, {"SPY": 1}
    )
    assert haa_runner.call_count == 0

    output = capsys.readouterr().out
    assert "리밸런싱 리포트" in output
    assert "SPY:" in output
