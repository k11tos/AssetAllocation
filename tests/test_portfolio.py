#!/usr/bin/python3
"""
Tests for portfolio rebalancing functionality
"""

import pytest

from portfolio import calculate_rebalancing


class TestRebalancing:
    """리밸런싱 계산 테스트"""

    def test_calculate_rebalancing_basic(self):
        """기본 리밸런싱 계산 테스트"""
        allocation = {"SPY": 25.0, "IWM": 25.0}
        current_prices = {"SPY": 450.0, "IWM": 200.0}
        current_balances = {"SPY": 10, "IWM": 5}

        result = calculate_rebalancing(
            allocation, current_prices, current_balances
        )

        # 결과가 딕셔너리인지 확인
        assert isinstance(result, dict)

        # 모든 필수 필드가 있는지 확인
        for ticker, info in result.items():
            assert "current_value" in info
            assert "target_value" in info
            assert "current_quantity" in info
            assert "target_quantity" in info
            assert "quantity_diff" in info
            assert "action" in info
            assert "price" in info
            assert "target_allocation_pct" in info
            assert "current_allocation_pct" in info

    def test_calculate_rebalancing_with_explicit_portfolio_value(self):
        """명시적 포트폴리오 가치를 사용한 테스트"""
        allocation = {"SPY": 100.0}
        current_prices = {"SPY": 400.0}
        current_balances = {"SPY": 10}

        result = calculate_rebalancing(
            allocation,
            current_prices,
            current_balances,
            total_portfolio_value=50000.0,
        )

        assert result["SPY"]["target_value"] == 50000.0
        assert result["SPY"]["target_quantity"] == 125  # 50000 / 400

    def test_calculate_rebalancing_buy_action(self):
        """매수 액션이 올바르게 계산되는지 테스트"""
        # 현재: SPY 5주 = $500, 총 포트폴리오 가치 = $500
        # 목표: SPY 80% 비중이므로 목표 가치 = $500 * 0.8 = $400
        # 하지만 이미 $500이 있으므로 매수가 아닌 매도여야 함
        # 매수 케이스를 만들기 위해 총 포트폴리오 가치를 명시적으로 큰 값으로 설정
        allocation = {"SPY": 80.0}
        current_prices = {"SPY": 100.0}
        current_balances = {"SPY": 5}  # 현재 가치: $500

        # 총 포트폴리오 가치를 $1000으로 설정하면 목표는 $800이므로 매수가 필요
        result = calculate_rebalancing(
            allocation,
            current_prices,
            current_balances,
            total_portfolio_value=1000.0,
        )

        # 목표 비중이 80%, 총 가치가 $1000이면 목표 가치는 $800이므로 매수가 필요
        assert result["SPY"]["action"] == "매수"
        assert result["SPY"]["quantity_diff"] > 0

    def test_calculate_rebalancing_sell_action(self):
        """매도 액션이 올바르게 계산되는지 테스트"""
        allocation = {"SPY": 20.0}
        current_prices = {"SPY": 100.0}
        current_balances = {"SPY": 10}  # 현재 가치: $1000

        result = calculate_rebalancing(
            allocation, current_prices, current_balances
        )

        # 목표 비중이 20%이므로 일부 주식을 매도해야 함
        assert result["SPY"]["action"] == "매도"
        assert result["SPY"]["quantity_diff"] < 0

    def test_calculate_rebalancing_hold_action(self):
        """유지 액션이 올바르게 계산되는지 테스트"""
        allocation = {"SPY": 100.0}
        current_prices = {"SPY": 100.0}
        current_balances = {"SPY": 10}  # 현재 가치: $1000

        # 목표 비중이 100%이고 현재도 100%이면 유지
        result = calculate_rebalancing(
            allocation,
            current_prices,
            current_balances,
            total_portfolio_value=1000.0,
        )

        # 목표 수량과 현재 수량이 거의 같으면 유지
        assert result["SPY"]["quantity_diff"] == 0
        assert result["SPY"]["action"] == "유지"

    def test_calculate_rebalancing_zero_price(self):
        """가격이 0인 경우 처리 테스트"""
        allocation = {"SPY": 100.0}
        current_prices = {"SPY": 0.0}
        current_balances = {"SPY": 10}

        result = calculate_rebalancing(
            allocation, current_prices, current_balances
        )

        assert result["SPY"]["target_quantity"] == 0
        assert result["SPY"]["current_quantity"] == 10
        # 가격이 0이고 목표 수량이 0이면 매도 또는 유지
        # FIX: 할당 비율이 존재하는데 가격이 0인 경우 데이터 부재로 간주
        assert result["SPY"]["action"] == "가격 정보 없음"

    def test_calculate_rebalancing_multiple_assets(self):
        """여러 자산을 포함한 리밸런싱 테스트"""
        allocation = {"SPY": 40.0, "IWM": 30.0, "TLT": 30.0}
        current_prices = {"SPY": 400.0, "IWM": 200.0, "TLT": 100.0}
        current_balances = {"SPY": 5, "IWM": 10, "TLT": 20}

        result = calculate_rebalancing(
            allocation, current_prices, current_balances
        )

        # 모든 자산에 대한 정보가 있는지 확인
        assert len(result) == 3
        assert "SPY" in result
        assert "IWM" in result
        assert "TLT" in result

    def test_calculate_rebalancing_allocation_pct(self):
        """목표 비중과 현재 비중이 올바르게 계산되는지 테스트"""
        allocation = {"SPY": 60.0}
        current_prices = {"SPY": 100.0}
        current_balances = {"SPY": 5}  # 현재 가치: $500

        result = calculate_rebalancing(
            allocation, current_prices, current_balances
        )

        assert result["SPY"]["target_allocation_pct"] == 60.0
        assert result["SPY"]["current_allocation_pct"] == pytest.approx(
            100.0, rel=1e-6
        )  # 현재는 100%
