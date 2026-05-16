"""Focused TwelveData behavior tests for scheduled multi-strategy runs."""

import pandas as pd

from exceptions import DataRetrievalError
from services.data_service import TwelveDataPriceProvider, _MinuteCreditLimiter


class TestTwelveDataRateLimitAndErrors:
    def test_rate_limit_is_shared_by_default_across_provider_instances(self, monkeypatch):
        clock = {"now": 0.0}
        slept = []

        def fake_time():
            return clock["now"]

        def fake_sleep(seconds):
            slept.append(seconds)
            clock["now"] += seconds

        TwelveDataPriceProvider._shared_limiters.clear()
        try:
            monkeypatch.setattr("services.data_service.time.time", fake_time)
            monkeypatch.setattr("services.data_service.time.sleep", fake_sleep)

            provider_1 = TwelveDataPriceProvider(
                "key", max_credits_per_minute=2, request_sleep_seconds=65
            )
            provider_2 = TwelveDataPriceProvider(
                "key", max_credits_per_minute=2, request_sleep_seconds=65
            )

            assert provider_1._get_limiter() is provider_2._get_limiter()

            def fake_fetch(symbol):
                return pd.Series([100.0], index=pd.to_datetime(["2026-01-02"]), name=symbol)

            provider_1._fetch_symbol = fake_fetch
            provider_2._fetch_symbol = fake_fetch

            provider_1.fetch(["SPY", "IWM"])
            provider_2.fetch(["TIP"])

            assert len(slept) == 1
            assert slept[0] >= 60.0
        finally:
            TwelveDataPriceProvider._shared_limiters.clear()

    def test_error_payload_with_status_error_or_429_raises_clear_message(self, monkeypatch):
        class _Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "status": "error",
                    "code": 429,
                    "message": "You have run out of API credits for the current minute.",
                }

        monkeypatch.setattr("services.data_service.requests.get", lambda *args, **kwargs: _Resp())

        provider = TwelveDataPriceProvider(
            "key",
            limiter=_MinuteCreditLimiter(
                max_credits_per_minute=10,
                request_sleep_seconds=65,
                time_func=lambda: 0.0,
                sleep_func=lambda _seconds: None,
            ),
        )

        try:
            provider.fetch(["TIP"])
            raised = False
        except DataRetrievalError as exc:
            raised = True
            assert "TIP" in str(exc)
            assert "run out of API credits" in str(exc)

        assert raised
