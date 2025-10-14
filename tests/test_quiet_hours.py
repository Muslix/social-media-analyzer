from datetime import datetime, UTC

from src.services.quiet_hours import QuietHoursManager


def make_manager():
    config = {
        "US": {
            "timezone": "America/New_York",
            "ranges": [("00:00", "06:00"), ("22:00", "23:00")],
        },
        "EU": {
            "timezone": "Europe/Berlin",
            "ranges": [("02:00", "05:00")],
        },
    }
    return QuietHoursManager(config)


def test_is_quiet_inside_window():
    manager = make_manager()
    dt = datetime(2024, 1, 1, 5, 0, tzinfo=UTC)  # Midnight New York -> 00:00 local
    assert manager.is_quiet("US", dt) is True


def test_is_not_quiet_outside_window():
    manager = make_manager()
    dt = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)  # 07:00 New York
    assert manager.is_quiet("US", dt) is False


def test_cross_midnight_window():
    config = {
        "LABEL": {
            "timezone": "Europe/Berlin",
            "ranges": [("22:00", "02:00")],
        }
    }
    manager = QuietHoursManager(config)
    dt = datetime(2024, 1, 1, 22, 30, tzinfo=UTC)  # 23:30 Berlin
    seconds, resume_at = manager.time_until_available("LABEL", dt)
    assert seconds is not None and seconds > 0
    assert resume_at is not None
    assert manager.is_quiet("LABEL", dt)
