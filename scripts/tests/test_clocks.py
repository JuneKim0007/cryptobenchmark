import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import clocks

SCALING = "cpu0 1 sched_pixel 422000 2246000 2246000\ncpu7 1 sched_pixel 533000 3782000 3782000\n"
PINNED = "cpu0 1 performance 2246000 2246000 2246000\ncpu1 0 - - - -\n"


def test_a_raised_floor_is_not_a_lock():
    assert clocks.locked([clocks.parse(SCALING)]) is False


def test_floor_equal_to_ceiling_on_every_online_core_is_a_lock():
    assert clocks.locked([clocks.parse(PINNED), clocks.parse(PINNED)]) is True


def test_unreadable_is_unknown_not_locked():
    assert clocks.locked([clocks.parse("cpu0 1 - - - -\n")]) is None


def test_a_lock_released_mid_run_is_not_a_lock(tmp_path):
    path = clocks.write(tmp_path / clocks.CLOCKS, clocks.parse(PINNED), clocks.parse(SCALING))
    assert clocks.runtime_locked([path]) == "false"


def test_an_unreadable_cpu_directory_yields_no_cores():
    assert clocks.parse("cpu[0-9]* 1 - - - -\n") == []
    assert clocks.parse(SCALING)[1]["index"] == 7 and clocks.parse(SCALING)[1]["cpuMaxKhz"] == 3782000
