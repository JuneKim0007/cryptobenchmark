"""python3 scripts/tests/test_manifest.py"""
import json
import pathlib
import sys
import tempfile

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from device.identity import DeviceIdError, device_id  # noqa: E402
from results.manifest import manifest  # noqa: E402
from results import run_inputs  # noqa: E402

RUNTIME = {"model": "probed", "sdkInt": 36, "fingerprint": "a/b/c:16/X/1:user/release-keys"}
PROBE = {"schemaVersion": 1, "runtime": RUNTIME, "providers": [
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
    (results / "global.yaml").write_text("schemaVersion: 1\nproviders: {bundled: [{artifact: 'g:a:1', create: X}]}\n")
    manifest(results, mode, results / "global.yaml", files)
    return yaml.safe_load((results / "manifest.yaml").read_text())


def test_a_run_with_estimated_energy_says_so_and_a_measured_one_is_as_it_was():
    with tempfile.TemporaryDirectory() as temporary:
        results = pathlib.Path(temporary)
        files = layout(results, measured=True)
        files["energy"] = results / "benchmark/energy.json"
        files["energy"].write_text(json.dumps({"source": "rails", "kind": "measured"}))
        assert "energy" not in written(results, "device", files)
        files["energy"].write_text(json.dumps({"source": "manafa", "kind": "estimated"}))
        assert written(results, "device", files)["energy"] == {"source": "manafa", "kind": "estimated"}


def test_problems_the_run_survived_are_recorded_and_a_clean_run_has_none():
    with tempfile.TemporaryDirectory() as temporary:
        results = pathlib.Path(temporary)
        files = layout(results, measured=True)
        assert "problems" not in written(results, "device", files)
        (results / "global.yaml").write_text("schemaVersion: 1\n")
        manifest(results, "device", results / "global.yaml", files, ["energy_failed: x", "not_measured: c"])
        assert yaml.safe_load((results / "manifest.yaml").read_text())["problems"] == ["energy_failed: x", "not_measured: c"]


def test_configure_only_lists_no_stage_that_did_not_run():
    with tempfile.TemporaryDirectory() as temporary:
        results = pathlib.Path(temporary)
        document = written(results, "host", layout(results, measured=False))
        assert document["schemaVersion"] == 1 and document["mode"] == "host"
        assert list(document["files"]) == ["probe", "trial", "inventory", "effective"]
        assert document["runtime"] == RUNTIME
        assert document["counts"] == {}
        assert document["inputs"] == run_inputs.digests(results / "global.yaml") and set(document["inputs"]) == {"bundled", "config"}


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


def test_the_device_id_comes_from_the_probe_even_when_measured():
    with tempfile.TemporaryDirectory() as temporary:
        results = pathlib.Path(temporary)
        assert written(results, "device", layout(results, measured=True))["deviceId"] == device_id(RUNTIME)


def test_a_probe_without_the_build_identity_writes_no_manifest():
    with tempfile.TemporaryDirectory() as temporary:
        results = pathlib.Path(temporary)
        files = layout(results, measured=False)
        files["probe"].write_text(yaml.safe_dump({"runtime": {"model": "probed", "sdkInt": 36}}))
        try:
            written(results, "device", files)
        except DeviceIdError as error:
            assert "fingerprint" in str(error) and not (results / "manifest.yaml").exists()
        else:
            raise AssertionError("expected device_id_fields_missing")


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


def test_the_display_units_are_recorded_from_effective_yaml():
    with tempfile.TemporaryDirectory() as temporary:
        results = pathlib.Path(temporary)
        files = layout(results, measured=False)
        assert "units" not in written(results, "host", files)
        files["effective"].write_text(yaml.safe_dump({"analysis": {"units": {"latency": "us", "throughput": "ops/s"}}}))
        assert written(results, "host", files)["units"] == {"latency": "us", "throughput": "ops/s"}


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"ok: {len(tests)} tests")
