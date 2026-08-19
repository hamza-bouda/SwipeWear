from datetime import datetime, timezone

from scripts.run_service import seconds_until_daily_run


def test_daily_delay_uses_same_day_when_time_is_ahead() -> None:
    now = datetime(2026, 8, 19, 18, 30, tzinfo=timezone.utc)
    assert seconds_until_daily_run(now, 19, 0) == 30 * 60


def test_daily_delay_rolls_to_tomorrow_when_time_has_passed() -> None:
    now = datetime(2026, 8, 19, 19, 30, tzinfo=timezone.utc)
    assert seconds_until_daily_run(now, 19, 0) == 23.5 * 60 * 60
