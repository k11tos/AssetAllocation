#!/usr/bin/python3
"""Shared helpers for strategy execution result export and comparison."""

import json
import os
from datetime import datetime
from typing import Any, Dict, List


def build_execution_output_data(results: Dict[str, Any]) -> Dict[str, Any]:
    """Build the standard JSON payload for strategy execution results."""
    return {
        "timestamp": datetime.now().isoformat(),
        "strategies": results,
    }


def save_execution_output_json(results: Dict[str, Any], file_path: str) -> None:
    """Save strategy execution results to a JSON file."""
    output_data = build_execution_output_data(results)
    output_dir = os.path.dirname(file_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(output_data, file, indent=2, ensure_ascii=False)


def load_execution_output_json(file_path: str) -> Dict[str, Any]:
    """Load saved strategy execution results from JSON."""
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Compare file must contain a JSON object")

    strategies = data.get("strategies")
    if not isinstance(strategies, dict):
        raise ValueError("Compare file must include 'strategies' as an object")

    return data


def format_execution_diff_summary(
    previous_data: Dict[str, Any], current_results: Dict[str, Any]
) -> str:
    """Summarize differences between previous and current execution results."""
    previous_strategies = previous_data.get("strategies", {})
    current_strategies = current_results

    previous_names = set(previous_strategies)
    current_names = set(current_strategies)

    added_strategies = sorted(current_names - previous_names)
    removed_strategies = sorted(previous_names - current_names)
    common_strategies = sorted(previous_names & current_names)

    output: List[str] = []
    output.append("Execution Result Diff")
    output.append("=" * 60)
    output.append(f"Added strategies: {len(added_strategies)}")
    output.append(f"Removed strategies: {len(removed_strategies)}")

    if added_strategies:
        output.append(f"  + {', '.join(added_strategies)}")
    if removed_strategies:
        output.append(f"  - {', '.join(removed_strategies)}")

    changed_strategies: List[str] = []
    unchanged_strategies: List[str] = []
    changed_entries = 0
    unchanged_entries = 0

    for strategy_name in common_strategies:
        previous_allocation = previous_strategies.get(strategy_name)
        current_allocation = current_strategies.get(strategy_name)

        if previous_allocation == current_allocation:
            unchanged_strategies.append(strategy_name)
            if isinstance(current_allocation, dict):
                unchanged_entries += len(current_allocation)
            continue

        changed_strategies.append(strategy_name)
        output.append(f"\n{strategy_name}:")
        output.append("-" * 40)

        if not isinstance(previous_allocation, dict) or not isinstance(
            current_allocation, dict
        ):
            output.append(
                f"  Changed result: {previous_allocation} -> {current_allocation}"
            )
            changed_entries += 1
            continue

        previous_assets = set(previous_allocation)
        current_assets = set(current_allocation)

        added_assets = sorted(current_assets - previous_assets)
        removed_assets = sorted(previous_assets - current_assets)
        common_assets = sorted(previous_assets & current_assets)

        for asset in added_assets:
            output.append(
                f"  + Added asset {asset}: {current_allocation[asset]:.2f}%"
            )
            changed_entries += 1
        for asset in removed_assets:
            output.append(
                f"  - Removed asset {asset}: {previous_allocation[asset]:.2f}%"
            )
            changed_entries += 1

        for asset in common_assets:
            previous_value = previous_allocation[asset]
            current_value = current_allocation[asset]
            if previous_value == current_value:
                unchanged_entries += 1
                continue

            delta = current_value - previous_value
            output.append(
                f"  * {asset}: {previous_value:.2f}% -> "
                f"{current_value:.2f}% ({delta:+.2f}%)"
            )
            changed_entries += 1

    output.append("")
    output.append(f"Changed strategies: {len(changed_strategies)}")
    output.append(f"Unchanged strategies: {len(unchanged_strategies)}")
    output.append(f"Changed allocation entries: {changed_entries}")
    output.append(f"Unchanged allocation entries: {unchanged_entries}")

    return "\n".join(output)
