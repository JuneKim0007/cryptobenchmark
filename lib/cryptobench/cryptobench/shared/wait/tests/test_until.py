"""until() on a fake clock: checks first, returns at the first accepted value, stops at the deadline, sleeps min(every, left)."""
from cryptobench.shared.wait.until import until
from fake_clock import FakeClock


def counting(values):
    seen = iter(values)
    return lambda: next(seen)


def test_a_condition_already_true_returns_without_sleeping():
    clock = FakeClock()
    assert until(lambda: "device", lambda v: v == "device", 10, 60, clock) == ("device", 0.0, True)
    assert clock.slept == []


def test_it_returns_at_the_first_accepted_value():
    clock = FakeClock()
    waited = until(counting([1, 2, 3, 4]), lambda v: v >= 3, 10, 60, clock)
    assert waited == (3, 20.0, True) and clock.slept == [10, 10]


def test_past_the_deadline_it_returns_the_last_value_unmet():
    clock = FakeClock()
    waited = until(counting(range(100)), lambda _v: False, 10, 25, clock)
    assert waited == (3, 25.0, False) and clock.slept == [10, 10, 5]


def test_a_zero_bound_checks_once():
    clock = FakeClock()
    assert until(lambda: None, lambda v: v is not None, 1, 0, clock) == (None, 0.0, False) and clock.slept == []


def test_a_slow_check_shortens_the_sleep_to_what_is_left():
    clock = FakeClock()

    def slow():
        clock.now += 4
        return None
    waited = until(slow, lambda v: v is not None, 10, 12, clock)
    assert clock.slept == [8] and waited.seconds == 16 and not waited.met
