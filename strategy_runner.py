"""Shared strategy execution orchestration helpers."""

from typing import Callable, Dict, Mapping, Optional

StrategyResult = Optional[Dict[str, float]]
StrategyRunner = Callable[[], StrategyResult]
StrategyRunnerMap = Mapping[str, StrategyRunner]


def get_available_strategy_runners(
    strategy_runners: StrategyRunnerMap,
) -> Dict[str, StrategyRunner]:
    """Return a concrete strategy runner mapping."""
    return dict(strategy_runners)


def run_strategy(
    strategy_name: str,
    strategy_runners: StrategyRunnerMap,
) -> StrategyResult:
    """Run a single strategy safely.

    Unknown strategy names raise KeyError.
    Execution failures return None.
    """
    runner = get_available_strategy_runners(strategy_runners)[strategy_name]

    try:
        return runner()
    except Exception:
        return None


def run_selected_strategies(
    requested_strategies: list[str],
    strategy_runners: StrategyRunnerMap,
) -> Dict[str, StrategyResult]:
    """Run each requested strategy while isolating failures per strategy."""
    available_runners = get_available_strategy_runners(strategy_runners)

    results: Dict[str, StrategyResult] = {}
    for strategy_name in requested_strategies:
        results[strategy_name] = run_strategy(strategy_name, available_runners)

    return results
