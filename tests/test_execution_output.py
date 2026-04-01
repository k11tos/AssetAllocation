#!/usr/bin/python3
"""Focused regression tests for execution_output compact diff formatting."""

import datetime
from zoneinfo import ZoneInfo

import execution_output
from execution_output import (
    build_execution_status_metadata,
    build_execution_output_data,
    format_compact_execution_diff_summary,
)


def test_compact_diff_marks_added_strategy_with_plus() -> None:
    previous = {"timestamp": "2026-01-01T00:00:00", "strategies": {}}
    current = {"HAA": {"SPY": 100.0}}

    summary = format_compact_execution_diff_summary(previous, current)

    assert summary is not None
    assert "- [+] HAA: strategy added" in summary


def test_compact_diff_marks_removed_strategy_with_minus() -> None:
    previous = {
        "timestamp": "2026-01-01T00:00:00",
        "strategies": {"HAA": {"SPY": 100.0}},
    }
    current = {}

    summary = format_compact_execution_diff_summary(previous, current)

    assert summary is not None
    assert "- [-] HAA: strategy removed" in summary


def test_compact_diff_marks_changed_strategy_with_tilde() -> None:
    previous = {
        "timestamp": "2026-01-01T00:00:00",
        "strategies": {"HAA": {"SPY": 60.0, "IEF": 40.0}},
    }
    current = {"HAA": {"SPY": 55.0, "IEF": 45.0}}

    summary = format_compact_execution_diff_summary(previous, current)

    assert summary is not None
    assert "- [~] HAA:" in summary


def test_compact_diff_returns_none_when_no_changes() -> None:
    previous = {
        "timestamp": "2026-01-01T00:00:00",
        "strategies": {"HAA": {"SPY": 100.0}},
    }
    current = {"HAA": {"SPY": 100.0}}

    summary = format_compact_execution_diff_summary(previous, current)

    assert summary is None


def test_compact_diff_includes_truncation_line_when_strategy_highlights_limited() -> None:
    previous = {
        "timestamp": "2026-01-01T00:00:00",
        "strategies": {
            "BAA": {"QQQ": 100.0},
            "HAA": {"SPY": 100.0},
            "KAW": {"TIGER S&P500": 100.0},
        },
    }
    current = {"HAA": {"SPY": 90.0, "IEF": 10.0}, "LAA": {"IWD": 100.0}}

    summary = format_compact_execution_diff_summary(
        previous,
        current,
        max_strategy_highlights=1,
        max_asset_highlights_per_strategy=1,
    )

    assert summary is not None
    assert "4 strategies changed" in summary
    assert "- ... and 1 more strategy changes" in summary


def test_get_execution_now_uses_asia_seoul_timezone() -> None:
    current = execution_output.get_execution_now()

    assert isinstance(current.tzinfo, ZoneInfo)
    assert current.tzinfo.key == "Asia/Seoul"


def test_build_execution_output_data_uses_timezone_aware_timestamp(monkeypatch) -> None:
    fixed_now = datetime.datetime(2026, 4, 1, 8, 30, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    monkeypatch.setattr(execution_output, "get_execution_now", lambda: fixed_now)

    payload = build_execution_output_data({"HAA": {"SPY": 100.0}})

    assert payload["timestamp"] == "2026-04-01T08:30:00+09:00"
    assert payload["status"] == "success"
    assert payload["stages"]["strategy_execution"]["status"] == "success"
    assert payload["stages"]["snapshot_save"]["status"] == "skipped"
    assert payload["errors"] == []


def test_build_execution_status_metadata_marks_partial_failure_for_mixed_results() -> None:
    metadata = build_execution_status_metadata(
        {"HAA": {"SPY": 100.0}, "KAW": None}
    )

    assert metadata["status"] == "partial_failure"
    assert metadata["stages"]["strategy_execution"]["status"] == "partial_failure"
    assert metadata["errors"] == [
        {"stage": "strategy_execution", "message": "1 of 2 strategies failed"}
    ]


def test_build_execution_status_metadata_treats_non_core_failure_as_partial_failure() -> None:
    metadata = build_execution_status_metadata(
        {"HAA": {"SPY": 100.0}},
        stage_overrides={
            "snapshot_save": {"status": "success"},
            "notification_reporting": {
                "status": "failure",
                "error": "notification boom",
            },
        },
    )

    assert metadata["status"] == "partial_failure"
    assert metadata["stages"]["notification_reporting"]["status"] == "failure"
    assert metadata["errors"] == [
        {"stage": "notification_reporting", "message": "notification boom"}
    ]
