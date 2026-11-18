"""The campaign audit over a hand-made results root: read only, one audit.yaml."""
import json

import yaml

from cryptobench.shared import paths
from cryptobench.stages.measurement.session import blocks
from cryptobench.stages.measurement.validation import audit

RUN = {"passes": {"energy": {"samples": 3, "minWindowSeconds": 5}}}


def case_file(path, case, median):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"benchmarks": [{"name": f"measure[{case}]", "repeatIterations": 10**6, "warmupIterations": 1,
                                                "metrics": {"timeNs": {"runs": [median] * 3}}}]}))


def unit(root, medians):
    """One energy pass of len(medians) runs, cases a and b; a's medians as given; one rejected attempt and one relaunch of a."""
    folder = root / "dev/suite"
    (folder / "manifest.yaml").parent.mkdir(parents=True)
    (folder / "manifest.yaml").write_text("{}\n")
    pass_folder = paths.RunTree(folder).benchmark.root / "energy"
    processes = []
    for n, median in enumerate(medians, 1):
        into = pass_folder / f"process-{n}"
        case_file(into / "cases/a.json", "a", median)
        case_file(into / "cases/b.json", "b", 100.0)
        (into / "order.txt").write_text("a\nb\n")
        (into / "energy-samples.yaml").write_text(yaml.safe_dump({"cases": {"b": {"samples": 3, "windowSeconds": 1.0, "shortWindow": n == 1}}}))
        processes.append({"repetition": n, "folder": into.relative_to(pass_folder).as_posix(), "problems": [],
                          "relaunched": [{"case": "a", "attempt": 1, "code": "miscalibrated"}] if n == 2 else [],
                          "files": blocks.run_files(into, pass_folder)})
    record = {"schemaVersion": blocks.SCHEMA, "pass": "energy", "block": 1, "identity": {"run": RUN}, "processes": processes}
    (pass_folder / "blocks").mkdir()
    (pass_folder / "blocks/block-1.yaml").write_text(yaml.safe_dump(record))
    why = folder / "rejected/20261118T000000Z/energy/process-2/why.yaml"
    why.parent.mkdir(parents=True)
    why.write_text(yaml.safe_dump({"case": "a", "run": "energy/process-2", "attempt": 1, "findings": []}))
    return folder


def test_the_audit_counts_runs_relaunches_rejections_and_flags_an_outlier_without_changing_the_results(tmp_path):
    folder = unit(tmp_path, [100.0, 101.0, 99.0, 100.0, 400.0])
    before = sorted((p, p.stat().st_mtime_ns) for p in tmp_path.rglob("*") if p.is_file())
    written = audit.written(tmp_path)
    assert sorted((p, p.stat().st_mtime_ns) for p in tmp_path.rglob("*") if p.is_file() and p != written) == before
    document = yaml.safe_load(written.read_text())
    energy = document["units"]["dev/suite"]["energy"]
    assert energy["runs"] == 5
    assert energy["cases"]["a"] == {"runsPresent": 5, "relaunched": 1, "rejected": 1, "findings": {}, "outliers": ["energy/process-5"]}
    assert energy["cases"]["b"] == {"runsPresent": 5, "relaunched": 0, "rejected": 0, "findings": {"short_window": 1}, "outliers": []}
    assert folder.joinpath("manifest.yaml").read_text() == "{}\n"


def test_superseded_units_are_not_audited_and_few_runs_flag_nothing(tmp_path):
    unit(tmp_path, [100.0, 400.0])
    (tmp_path / "dev/suite/superseded/x").mkdir(parents=True)
    (tmp_path / "dev/suite/superseded/x/manifest.yaml").write_text("{}\n")
    document = audit.audit(tmp_path)
    assert list(document["units"]) == ["dev/suite"] and document["units"]["dev/suite"]["energy"]["cases"]["a"]["outliers"] == []
