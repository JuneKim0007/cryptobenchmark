import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import outliers


def test_clean_runs_are_all_kept():
    runs = [100.0, 101.0, 99.0, 100.5, 99.5] * 4
    assert outliers.split(runs) == (runs, [])


def test_a_spike_is_removed_and_the_rest_kept():
    runs = [100.0, 101.0, 99.0, 100.5, 99.5] * 4 + [400.0]
    kept, removed = outliers.split(runs)
    assert removed == [400.0] and len(kept) == 20


def test_more_than_twenty_removals_fall_back_to_every_run():
    runs = [100.0 + i * 0.001 for i in range(30)] + [100.0 * 1.5 ** i for i in range(1, 30)]
    kept, removed = outliers.split(runs)
    assert removed == [] and kept == runs


def test_a_spike_is_found_in_a_small_sample():
    kept, removed = outliers.split([100.0, 101.0, 99.0, 100.0, 102.0, 98.0, 100.0, 101.0, 99.0, 1000.0])
    assert removed == [1000.0] and len(kept) == 9
