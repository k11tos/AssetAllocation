#!/usr/bin/python3
"""Unit tests for shared strategy execution orchestration."""

from strategy_runner import (
    get_available_strategy_runners,
    run_selected_strategies,
    run_strategy,
)


def test_get_available_strategy_runners_returns_copy():
    source = {"HAA": lambda: {"SPY": 100.0}}

    runners = get_available_strategy_runners(source)

    assert runners == source
    assert runners is not source


def test_run_strategy_returns_none_on_failure():
    def failing_runner():
        raise RuntimeError("boom")

    result = run_strategy("HAA", {"HAA": failing_runner})

    assert result is None


def test_run_selected_strategies_continues_when_one_strategy_fails():
    results = run_selected_strategies(
        ["HAA", "KAW"],
        {
            "HAA": lambda: {"SPY": 100.0},
            "KAW": lambda: 1 / 0,
        },
    )

    assert results["HAA"] == {"SPY": 100.0}
    assert results["KAW"] is None
