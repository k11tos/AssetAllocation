#!/usr/bin/python3
"""Shared helpers for strategy execution result export and comparison."""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

EXECUTION_TIMEZONE = ZoneInfo("Asia/Seoul")


def get_execution_now() -> datetime:
    """Return the current execution time in Korea Standard Time."""
    return datetime.now(EXECUTION_TIMEZONE)


def build_execution_output_data(results: Dict[str, Any]) -> Dict[str, Any]:
    """Build the standard JSON payload for strategy execution results."""
    metadata = build_execution_status_metadata(results)
    return {
        "timestamp": get_execution_now().isoformat(),
        "strategies": results,
        "status": metadata["status"],
        "stages": metadata["stages"],
        "errors": metadata["errors"],
    }


def build_execution_status_metadata(
    results: Dict[str, Any],
    *,
    stage_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build structured execution status metadata for persisted snapshots."""
    stage_overrides = stage_overrides or {}
    strategy_values = list(results.values())
    successful_count = sum(value is not None for value in strategy_values)

    if not strategy_values or successful_count == 0:
        strategy_status = "failure"
        strategy_error = "No strategy result was produced"
    elif successful_count == len(strategy_values):
        strategy_status = "success"
        strategy_error = None
    else:
        strategy_status = "partial_failure"
        strategy_error = (
            f"{len(strategy_values) - successful_count} of "
            f"{len(strategy_values)} strategies failed"
        )

    stages: Dict[str, Dict[str, Any]] = {
        "strategy_execution": {"status": strategy_status},
        "snapshot_save": {"status": "skipped"},
        "notification_reporting": {"status": "skipped"},
    }
    if strategy_error:
        stages["strategy_execution"]["error"] = strategy_error

    for stage_name, stage_data in stage_overrides.items():
        current = stages.get(stage_name, {})
        current.update(stage_data)
        stages[stage_name] = current

    errors = [
        {"stage": stage_name, "message": stage_data["error"]}
        for stage_name, stage_data in stages.items()
        if isinstance(stage_data, dict) and stage_data.get("error")
    ]

    core_stage_statuses = [
        stages.get("strategy_execution", {}).get("status"),
        stages.get("snapshot_save", {}).get("status"),
    ]
    non_core_stage_statuses = [
        stage_data.get("status")
        for stage_name, stage_data in stages.items()
        if stage_name not in {"strategy_execution", "snapshot_save"}
        and isinstance(stage_data, dict)
    ]

    if any(status == "failure" for status in core_stage_statuses):
        overall_status = "failure"
    elif any(status == "partial_failure" for status in core_stage_statuses):
        overall_status = "partial_failure"
    elif any(status == "failure" for status in non_core_stage_statuses):
        overall_status = "partial_failure"
    elif any(status == "partial_failure" for status in non_core_stage_statuses):
        overall_status = "partial_failure"
    else:
        overall_status = "success"

    return {"status": overall_status, "stages": stages, "errors": errors}


def save_execution_output_json(
    results: Dict[str, Any],
    file_path: str,
    stage_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
    """Save strategy execution results to a JSON file."""
    effective_stage_overrides: Dict[str, Dict[str, Any]] = {
        "snapshot_save": {"status": "success"}
    }
    if stage_overrides:
        effective_stage_overrides.update(stage_overrides)

    output_data = build_execution_output_data(results)
    metadata = build_execution_status_metadata(
        results, stage_overrides=effective_stage_overrides
    )
    output_data.update(metadata)
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


def format_compact_execution_diff_summary(
    previous_data: Dict[str, Any],
    current_results: Dict[str, Any],
    max_strategy_highlights: int = 3,
    max_asset_highlights_per_strategy: int = 2,
) -> Optional[str]:
    """Return a compact human-readable diff summary for report/message flows."""
    previous_strategies = previous_data.get("strategies", {})
    if not isinstance(previous_strategies, dict):
        raise ValueError("Previous execution payload must include strategies object")

    previous_names = set(previous_strategies)
    current_names = set(current_results)
    common_names = sorted(previous_names & current_names)

    changed_strategies = []
    changed_entries = 0
    strategy_highlights: List[str] = []

    def _count_changed_entries_for_strategy_payload(payload: Any) -> int:
        if isinstance(payload, dict):
            return len(payload)
        return 1

    for strategy_name in common_names:
        previous_allocation = previous_strategies.get(strategy_name)
        current_allocation = current_results.get(strategy_name)
        if previous_allocation == current_allocation:
            continue

        changed_strategies.append(strategy_name)

        if not isinstance(previous_allocation, dict) or not isinstance(
            current_allocation, dict
        ):
            changed_entries += 1
            strategy_highlights.append(f"{strategy_name}: result changed")
            continue

        previous_assets = set(previous_allocation)
        current_assets = set(current_allocation)
        asset_changes: List[str] = []

        added_assets = sorted(current_assets - previous_assets)
        removed_assets = sorted(previous_assets - current_assets)
        common_assets = sorted(previous_assets & current_assets)

        for asset in added_assets:
            changed_entries += 1
            if len(asset_changes) < max_asset_highlights_per_strategy:
                asset_changes.append(f"+{asset}")

        for asset in removed_assets:
            changed_entries += 1
            if len(asset_changes) < max_asset_highlights_per_strategy:
                asset_changes.append(f"-{asset}")

        for asset in common_assets:
            previous_value = previous_allocation[asset]
            current_value = current_allocation[asset]
            if previous_value == current_value:
                continue

            changed_entries += 1
            if len(asset_changes) < max_asset_highlights_per_strategy:
                delta = current_value - previous_value
                asset_changes.append(f"{asset} {delta:+.2f}%")

        if asset_changes:
            strategy_highlights.append(
                f"{strategy_name}: {', '.join(asset_changes)}"
            )
        else:
            strategy_highlights.append(f"{strategy_name}: allocation changed")

    # Added/removed strategies are meaningful strategy-level changes.
    added_strategies = sorted(current_names - previous_names)
    removed_strategies = sorted(previous_names - current_names)
    added_or_removed = set(added_strategies) | set(removed_strategies)
    changed_strategy_count = len(changed_strategies) + len(added_or_removed)

    for strategy_name in added_strategies:
        changed_entries += _count_changed_entries_for_strategy_payload(
            current_results.get(strategy_name)
        )

    for strategy_name in removed_strategies:
        changed_entries += _count_changed_entries_for_strategy_payload(
            previous_strategies.get(strategy_name)
        )

    if changed_strategy_count == 0:
        return None

    compact_lines = [
        (
            "Scheduled diff: "
            f"{changed_strategy_count} strategies changed, "
            f"{changed_entries} allocation entries changed"
        )
    ]

    for strategy_name in added_strategies[:max_strategy_highlights]:
        compact_lines.append(f"- [+] {strategy_name}: strategy added")
    for strategy_name in removed_strategies[:max_strategy_highlights]:
        compact_lines.append(f"- [-] {strategy_name}: strategy removed")

    for highlight in strategy_highlights[:max_strategy_highlights]:
        compact_lines.append(f"- [~] {highlight}")

    displayed_highlight_count = (
        min(len(added_strategies), max_strategy_highlights)
        + min(len(removed_strategies), max_strategy_highlights)
        + min(len(strategy_highlights), max_strategy_highlights)
    )
    remaining_highlight_count = changed_strategy_count - displayed_highlight_count
    if remaining_highlight_count > 0:
        compact_lines.append(
            f"- ... and {remaining_highlight_count} more strategy changes"
        )

    return "\n".join(compact_lines)
