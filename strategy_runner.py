"""Shared strategy execution orchestration helpers."""

import importlib
from typing import Callable, Dict, Optional

StrategyResult = Optional[Dict[str, float]]
StrategyRunner = Callable[[], StrategyResult]

_STRATEGY_REGISTRY: Dict[str, Dict[str, str]] = {
    "cli": {
        "HAA": "run_haa_strategy",
        "KAW": "run_kaw_strategy",
        "BAA": "run_baa_strategy",
        "VAA": "run_vaa_strategy",
        "LAA": "run_laa_strategy",
        "BDAA": "run_bdaa_strategy",
        "MDM": "run_mdm_strategy",
        "SECTOR_MOMENTUM": "run_sector_momentum_strategy",
    },
    "main": {
        "HAA": "execute_haa_strategy",
        "KAW": "execute_kaw_strategy",
        "SECTOR_MOMENTUM": "execute_sector_momentum_strategy",
    },
}

_ENTRYPOINT_MODULES = {
    "cli": "cli_strategy_executor",
    "main": "main",
}


def get_available_strategy_runners(entrypoint: str) -> Dict[str, StrategyRunner]:
    """Return the strategy runner mapping for an entrypoint."""
    if entrypoint not in _STRATEGY_REGISTRY:
        raise KeyError(f"Unknown entrypoint: {entrypoint}")

    module_name = _ENTRYPOINT_MODULES.get(entrypoint, entrypoint)
    module = importlib.import_module(module_name)
    mapping = _STRATEGY_REGISTRY[entrypoint]
    return {name: getattr(module, runner_name) for name, runner_name in mapping.items()}


def run_strategy(strategy_name: str, entrypoint: str) -> StrategyResult:
    """Run a single strategy safely.

    Unknown strategy names raise KeyError.
    Execution failures return None.
    """
    runner = get_available_strategy_runners(entrypoint)[strategy_name]

    try:
        return runner()
    except Exception:
        return None


def run_selected_strategies(
    requested_strategies: list[str],
    entrypoint: str,
) -> Dict[str, StrategyResult]:
    """Run each requested strategy while isolating failures per strategy."""
    # Validate entrypoint eagerly to preserve prior behavior even when
    # no strategies are requested.
    get_available_strategy_runners(entrypoint)
    return {
        strategy_name: run_strategy(strategy_name, entrypoint)
        for strategy_name in requested_strategies
    }
