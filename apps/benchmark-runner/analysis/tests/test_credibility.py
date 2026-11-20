import json
import random

import credibility
from cryptobench.shared.stats import inference
from cryptobench.shared.stats.equations import median_ranks

PROCESSES = 20


def case(cid, variant, samples, energy=None):
    metrics = {"timeNs": {"iterations": 10, "runs": samples}}
    if energy is not None:
        metrics["energyJ"] = {"runs": [energy], "kind": "measured"}
    return {"id": f"{cid}_{variant}", "variant": variant, "metrics": metrics}


def processes(tmp_path, ramp=0.3):
    """Item a: notFixed at 1.5x fixed; process p's time samples center on 100 + p. Item b: every process ramps up."""
    rng, files = random.Random(5), []
    for p in range(PROCESSES):
        steady = [100 + p + rng.gauss(0, 0.2) for _ in range(30)]
        drifting = [200 * (1 + ramp * i / 29) + rng.gauss(0, 0.2) for i in range(30)]
        cases = [case("a", "fixed", steady, energy=1e-5 * (1 + p / 100)), case("a", "notFixed", [1.5 * v for v in steady], energy=1.5e-5 * (1 + p / 100)),
                 case("b", "fixed", drifting)]
        file = tmp_path / f"process-{p + 1}.json"
        file.write_text(json.dumps({"cases": cases}))
        files.append(file)
    return files


def rows_by(rows, cid, metric):
    return next(r for r in rows if r["case"] == cid and r["metric"] == metric)


def test_each_process_is_one_value_and_the_interval_reads_its_binomial_ranks(tmp_path):
    _, rows, _ = credibility.build(processes(tmp_path))
    row = rows_by(rows, "a_fixed", "timeNs")
    low, high, coverage = median_ranks(PROCESSES)
    assert row["n"] == PROCESSES and row["ranks"] == [low, high] and row["coverage"] == coverage
    assert abs(row["median"] - (100 + (PROCESSES - 1) / 2)) < 0.5
    assert abs(row["ciLow"] - (100 + low - 1)) < 0.5 and abs(row["ciHigh"] - (100 + high - 1)) < 0.5
    assert rows_by(rows, "a_fixed", "energyJ")["withinCov"] is None


def test_a_known_ratio_comes_back_with_an_interval_around_it_and_a_large_effect(tmp_path):
    _, _, pairs = credibility.build(processes(tmp_path))
    assert {(p["pair"], p["metric"]) for p in pairs} == {("a", "timeNs"), ("a", "energyJ")}
    for pair in pairs:
        assert abs(pair["ratio"] - 1.5) < 1e-9 and pair["ratioLow"] <= 1.5 <= pair["ratioHigh"]
        assert pair["cliffsDelta"] == 1.0 and pair["magnitude"] == "large" and pair["mannWhitneyP"] < 1e-6


def test_a_case_whose_processes_drift_is_flagged_and_a_steady_one_is_not(tmp_path):
    _, rows, _ = credibility.build(processes(tmp_path))
    drifting, steady = rows_by(rows, "b_fixed", "timeNs"), rows_by(rows, "a_fixed", "timeNs")
    assert drifting["driftFlag"] and drifting["drifting"] == PROCESSES and drifting["driftRatio"] > 1.15
    assert not steady["driftFlag"] and steady["drifting"] == 0


def test_a_small_ramp_below_the_ratio_limit_is_not_drift(tmp_path):
    _, rows, _ = credibility.build(processes(tmp_path, ramp=0.03))
    assert rows_by(rows, "b_fixed", "timeNs")["drifting"] == 0


def test_the_report_records_the_seed_and_draws_a_qq_plot_per_case(tmp_path):
    out = tmp_path / "out"
    credibility.write(out, processes(tmp_path))
    data = json.loads((out / "credibility.json").read_text())
    assert data["bootstrap"] == {"seed": inference.BOOTSTRAP_SEED, "resamples": inference.BOOTSTRAP_RESAMPLES}
    assert f"seed {inference.BOOTSTRAP_SEED}" in (out / "credibility.md").read_text()
    assert sorted(p.name for p in (out / "qq").iterdir()) == ["a_fixed.png", "a_notFixed.png", "b_fixed.png"]


def test_one_process_still_writes_a_row_without_tests(tmp_path):
    _, rows, _ = credibility.build(processes(tmp_path)[:1])
    row = rows_by(rows, "a_fixed", "timeNs")
    assert row["n"] == 1 and row["shapiroP"] is None and row["qq"] is None


def test_too_few_processes_say_the_qq_score_is_not_meaningful(tmp_path):
    out = tmp_path / "out"
    credibility.write(out, processes(tmp_path)[:5])
    assert "n < 8: not meaningful" in (out / "credibility.md").read_text()
    assert not (out / "qq").exists()


def test_each_row_carries_r_its_critical_value_and_a_verdict(tmp_path):
    _, rows, _ = credibility.build(processes(tmp_path))
    row = rows_by(rows, "a_fixed", "timeNs")
    assert row["qqCritical"] == inference.qq_critical(PROCESSES) and row["qqPass"] == (row["qq"] >= row["qqCritical"])
