#!/usr/bin/python3
"""Unit tests for shared strategy execution orchestration."""

import sys
import types

import pytest

from strategy_runner import (
    get_available_strategy_runners,
    run_selected_strategies,
    run_strategy,
)


@pytest.fixture
def fake_cli_executor_module(monkeypatch):
    cli_executor_module = types.ModuleType("cli_strategy_executor")
    cli_executor_module.run_haa_strategy = lambda: {"SPY": 100.0}
    cli_executor_module.run_kaw_strategy = lambda: {"KAW": 100.0}
    cli_executor_module.run_baa_strategy = lambda: {"BAA": 100.0}
    cli_executor_module.run_vaa_strategy = lambda: {"VAA": 100.0}
    cli_executor_module.run_laa_strategy = lambda: {"LAA": 100.0}
    cli_executor_module.run_bdaa_strategy = lambda: {"BDAA": 100.0}
    cli_executor_module.run_mdm_strategy = lambda: {"MDM": 100.0}

    monkeypatch.setitem(sys.modules, "cli_strategy_executor", cli_executor_module)
    return cli_executor_module


def test_get_available_strategy_runners_resolves_registry(fake_cli_executor_module):
    runners = get_available_strategy_runners("cli")

    assert set(runners) == {"HAA", "KAW", "BAA", "VAA", "LAA", "BDAA", "MDM"}
    assert runners["HAA"]() == {"SPY": 100.0}


def test_run_strategy_returns_none_on_failure(fake_cli_executor_module):
    fake_cli_executor_module.run_haa_strategy = lambda: 1 / 0

    result = run_strategy("HAA", "cli")

    assert result is None


def test_run_selected_strategies_continues_when_one_strategy_fails(
    fake_cli_executor_module,
):
    fake_cli_executor_module.run_kaw_strategy = lambda: 1 / 0

    results = run_selected_strategies(["HAA", "KAW"], "cli")

    assert results["HAA"] == {"SPY": 100.0}
    assert results["KAW"] is None


def test_get_available_strategy_runners_raises_for_unknown_entrypoint():
    with pytest.raises(KeyError):
        get_available_strategy_runners("unknown")
