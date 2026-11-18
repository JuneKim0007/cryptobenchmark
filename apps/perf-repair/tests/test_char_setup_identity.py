"""Characterization (Py-P5): which manifest and run-folder fields the delta merge's setup fingerprint compares and which it ignores today, and that
the device stage reuses a stored benchmark whatever code digest --identify reports."""
import pytest
import yaml

from cryptobench.shared.paths import RunTree
from cryptobench.shared.document.document import read_yaml
from perfrepair.device import stage as device_stage
from perfrepair.device.setup_fingerprint import differing, fingerprint, provider_setup
from test_benchmark_gate import device  # noqa: F401
from test_device_stage import ALL_RAN, setup  # noqa: F401
from test_device_stage import device as stage


def edited(folder, manifest=lambda m: None, effective=lambda e: None, extra=None):
    m, e = read_yaml(RunTree(folder).manifest), read_yaml(folder / "configuration/effective.yaml")
    manifest(m), effective(e)
    if extra:
        (folder / extra[0]).write_text(extra[1])
        m["files"][extra[2]] = extra[0]
    RunTree(folder).manifest.write_text(yaml.safe_dump(m))
    (folder / "configuration/effective.yaml").write_text(yaml.safe_dump(e))


FIELDS = [
    ("deviceId", lambda f: edited(f, lambda m: m.update(deviceId="other")), ["deviceId"]),
    ("mode", lambda f: edited(f, lambda m: m.update(mode="host")), ["mode"]),
    ("runtime.sdkInt", lambda f: edited(f, lambda m: m["runtime"].update(sdkInt=35)), ["runtime.sdkInt"]),
    ("runtime.javaRuntimeVersion", lambda f: edited(f, lambda m: m["runtime"].update(javaRuntimeVersion="x")), ["runtime.javaRuntimeVersion"]),
    ("run.orderSeed", lambda f: edited(f, effective=lambda e: e["run"].update(orderSeed=3)), ["run.orderSeed"]),
    ("runtime.model ignored", lambda f: edited(f, lambda m: m["runtime"].update(model="other")), []),
    ("runtime.cpuLocked ignored", lambda f: edited(f, lambda m: m["runtime"].update(cpuLocked=True)), []),
    ("inputs ignored", lambda f: edited(f, lambda m: m.update(inputs={"bundled": "b", "config": "c"})), []),
    ("problems ignored", lambda f: edited(f, lambda m: m.update(problems=["energy_failed: x"])), []),
    ("effective outside run ignored", lambda f: edited(f, effective=lambda e: e.update(runId="other", providers={})), []),
    ("build facts ignored", lambda f: edited(f, extra=("discovery/facts.yaml", "schemaVersion: 1\nbuild: {securityPatch: 2099-01-01}\n", "facts")), []),
]


@pytest.mark.parametrize("name, edit, named", FIELDS, ids=[f[0] for f in FIELDS])
def test_today_setup_fingerprint_compares_these_fields_and_ignores_the_rest(device, name, edit, named):  # noqa: F811
    stored = fingerprint(device)
    edit(device)
    assert [line.split(":")[0] for line in differing(stored, fingerprint(device))] == named


def test_today_setup_fingerprint_has_no_code_digest_build_facts_or_suppress_errors(device):  # noqa: F811
    keys = set(fingerprint(device))
    assert not [k for k in keys if any(word in k.lower() for word in ("code", "harnessdigest", "suppress", "facts", "patch", "apex"))]
    assert {"deviceId", "mode", "bundled", "processes", "energy"} <= keys


def test_today_provider_setup_drops_run_prepared_processes_and_energy(device):  # noqa: F811
    assert not [k for k in provider_setup(device) if k.startswith(("run.", "prepared.")) or k in ("processes", "energy")]


def test_today_a_changed_code_digest_reuses_every_stage(setup, monkeypatch):  # noqa: F811
    root, config = setup
    real = device_stage.identify
    monkeypatch.setattr(device_stage, "identify", lambda *a, **k: {**real(*a, **k), "code": "first", "harness": "first"})
    assert stage(root, config).ran == ALL_RAN
    monkeypatch.setattr(device_stage, "identify", lambda *a, **k: {**real(*a, **k), "code": "second", "harness": "second"})
    assert stage(root, config).ran == []
