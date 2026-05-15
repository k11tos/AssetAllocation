import pytest

from portfolio import get_sector_momentum_allocation
from strategies.sector_momentum_strategy import SectorMomentumStrategy


@pytest.fixture
def strategy():
    return SectorMomentumStrategy()


def test_top_two_positive_momentum_etfs_selected(strategy):
    data = {
        "momentum_score": {"XLK": 0.3, "XLC": 0.2, "XLI": 0.1},
        "sma_12month": {"XLK": 100.0, "XLC": 100.0, "XLI": 100.0},
        "today_price": {"XLK": 110.0, "XLC": 120.0, "XLI": 130.0},
    }

    result = strategy.calculate_allocation(data)

    assert result == {"XLK": 50.0, "XLC": 50.0}


def test_negative_momentum_etfs_excluded(strategy):
    data = {
        "momentum_score": {"XLK": 0.25, "XLC": -0.1, "XLI": -0.01},
        "sma_12month": {"XLK": 100.0, "XLC": 100.0, "XLI": 100.0},
        "today_price": {"XLK": 110.0, "XLC": 110.0, "XLI": 110.0},
    }

    result = strategy.calculate_allocation(data)

    assert result == {"XLK": 50.0, "SGOV": 50.0}


def test_etf_below_12month_sma_excluded(strategy):
    data = {
        "momentum_score": {"XLK": 0.3, "XLC": 0.25, "XLI": 0.2},
        "sma_12month": {"XLK": 100.0, "XLC": 100.0, "XLI": 100.0},
        "today_price": {"XLK": 110.0, "XLC": 99.0, "XLI": 130.0},
    }

    result = strategy.calculate_allocation(data)

    assert result == {"XLK": 50.0, "XLI": 50.0}


def test_one_passing_etf_results_in_half_defensive(strategy):
    data = {
        "momentum_score": {"XLK": 0.3, "XLC": -0.2},
        "sma_12month": {"XLK": 100.0, "XLC": 100.0},
        "today_price": {"XLK": 101.0, "XLC": 101.0},
    }

    result = strategy.calculate_allocation(data)

    assert result == {"XLK": 50.0, "SGOV": 50.0}


def test_zero_passing_etfs_results_in_full_defensive(strategy):
    data = {
        "momentum_score": {"XLK": -0.3, "XLC": -0.2},
        "sma_12month": {"XLK": 100.0, "XLC": 100.0},
        "today_price": {"XLK": 101.0, "XLC": 101.0},
    }

    result = strategy.calculate_allocation(data)

    assert result == {"SGOV": 100.0}


def test_missing_etf_data_skipped_safely(strategy):
    data = {
        "momentum_score": {"XLK": 0.4, "XLC": 0.3, "XLI": 0.2},
        "sma_12month": {"XLK": 100.0, "XLI": 100.0},
        "today_price": {"XLK": 101.0, "XLC": 110.0},
    }

    result = strategy.calculate_allocation(data)

    assert result == {"XLK": 50.0, "SGOV": 50.0}


def test_portfolio_wrapper_calls_strategy():
    result = get_sector_momentum_allocation(
        momentum_score={"XLK": 0.3, "XLC": 0.2},
        sma_12month={"XLK": 100.0, "XLC": 100.0},
        today_price={"XLK": 110.0, "XLC": 120.0},
    )

    assert result == {"XLK": 50.0, "XLC": 50.0}
