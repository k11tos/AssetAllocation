#!/usr/bin/python3
"""Focused regression tests for execution_output compact diff formatting."""

from execution_output import format_compact_execution_diff_summary


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
