from types import SimpleNamespace

from src.services.interval_controller import IntervalController


def make_config(**overrides):
    defaults = {
        "REPEAT_DELAY": 600,
        "REPEAT_MIN_DELAY": None,
        "REPEAT_MAX_DELAY": None,
        "BLOCKED_BACKOFF_MIN": None,
        "BLOCKED_BACKOFF_MAX": None,
        "EMPTY_FETCH_THRESHOLD": 3,
        "EMPTY_FETCH_BACKOFF_MULTIPLIER": 1.5,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_compute_delay_uses_random_range():
    config = make_config(REPEAT_MIN_DELAY=420, REPEAT_MAX_DELAY=840)
    rng = __import__("random").Random(0)
    controller = IntervalController(config, rng=rng)

    delay, reasons = controller.compute_delay(blocked=False, consecutive_empty=0)
    assert 420 <= delay <= 840
    assert reasons["base"] == delay


def test_blocked_delay_exceeds_base():
    config = make_config(REPEAT_DELAY=600, BLOCKED_BACKOFF_MIN=900, BLOCKED_BACKOFF_MAX=1200)
    rng = __import__("random").Random(0)
    controller = IntervalController(config, rng=rng)

    delay, reasons = controller.compute_delay(blocked=True, consecutive_empty=0)
    assert delay >= 900
    assert reasons["blocked"] >= 900


def test_empty_backoff_scales_with_consecutive_empty():
    config = make_config(REPEAT_DELAY=600, EMPTY_FETCH_THRESHOLD=2, EMPTY_FETCH_BACKOFF_MULTIPLIER=2.0)
    controller = IntervalController(config, rng=__import__("random").Random(1))

    delay, reasons = controller.compute_delay(blocked=False, consecutive_empty=3)
    assert reasons["empty_backoff"] >= 1200
    assert delay == reasons["empty_backoff"]
