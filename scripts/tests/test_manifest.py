"""python3 scripts/tests/test_manifest.py"""
import json
import pathlib
import sys
import tempfile

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from pipeline import manifest  # noqa: E402

PROBE = {"schemaVersion": 1, "runtime": {"model": "probed"}, "providers": [
    {"name": "second", "precedence": 2, "services": [{"type": "t", "algorithm": "a"}]},
    {"name": "first", "precedence": 1, "services": [{"type": "t", "algorithm": "a"}, {"type": "t", "algorithm": "b"}]},
    {"name": "empty", "precedence": 3, "services": []},
]}


def layout(results, measured):
    files = {}
    for key, relative, document in (
            ("probe", "discovery/probe_20260101T000000Z.yaml", PROBE),
            ("trial", "discovery/trial_20260101T000000Z.yaml", {"schemaVersion": 1}),
            ("inventory", "configuration/inventory.yaml", {"schemaVersion": 1}),
            ("effective", "configuration/effective.yaml", {"schemaVersion": 1}),
            ("prepared", "preparation/prepared.yaml", {"cases": [{"id": "a"}, {"id": "b"}, {"id": "c"}]}),
            ("skipped", "preparation/skipped.yaml", {"skipped": [{"reason": "r"}]}),
            ("benchmark", "benchmark/benchmark.json", {"runtime": {"model": "measured"}, "cases": [{"id": "a"}, {"id": "b"}]})):
        if key in ("prepared", "skipped", "benchmark") and not measured:
            continue
        path = results / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document) if path.suffix == ".json" else yaml.safe_dump(document))
        files[key] = path
    return files


def written(results, mode, files):
    manifest(results, mode, results / "global.yaml", files)
    return yaml.safe_load((results / "manifest.yaml").read_text())


def test_configure_only_lists_no_stage_that_did_not_run():
    with tempfile.TemporaryDirectory() as temporary:
        results = pathlib.Path(temporary)
        document = written(results, "host", layout(results, measured=False))
        assert document["schemaVersion"] == 1 and document["mode"] == "host"
        assert list(document["files"]) == ["probe", "trial", "inventory", "effective"]
        assert document["runtime"] == {"model": "probed"}
        assert document["counts"] == {}


def test_providers_in_precedence_order_with_service_counts():
    with tempfile.TemporaryDirectory() as temporary:
        results = pathlib.Path(temporary)
        document = written(results, "host", layout(results, measured=False))
        assert document["providers"] == [{"name": "first", "precedence": 1, "serviceCount": 2},
                                         {"name": "second", "precedence": 2, "serviceCount": 1},
                                         {"name": "empty", "precedence": 3, "serviceCount": 0}]


def test_measured_run_takes_the_measured_runtime_and_counts():
    with tempfile.TemporaryDirectory() as temporary:
        results = pathlib.Path(temporary)
        document = written(results, "device", layout(results, measured=True))
        assert document["mode"] == "device"
        assert document["runtime"] == {"model": "measured"}
        assert document["counts"] == {"prepared": 3, "skipped": 1, "measured": 2}


def test_paths_are_relative_to_the_manifest_and_exist():
    with tempfile.TemporaryDirectory() as temporary:
        results = pathlib.Path(temporary)
        files = layout(results, measured=True)
        processes = []
        for n in (1, 2):
            process = results / f"benchmark/process-{n}/benchmark.json"
            process.parent.mkdir(parents=True)
            process.write_text("{}")
            processes.append(process)
        document = written(results, "host", dict(files, processes=processes))
        assert document["files"]["processes"] == ["benchmark/process-1/benchmark.json", "benchmark/process-2/benchmark.json"]
        for value in document["files"].values():
            for relative in value if isinstance(value, list) else [value]:
                assert not pathlib.PurePosixPath(relative).is_absolute() and (results / relative).is_file(), relative


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"ok: {len(tests)} tests")
