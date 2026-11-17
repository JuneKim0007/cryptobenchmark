"""discover's three entries on the host with a fake ProbeKt: discover_published stages and publishes;
discover_staged publishes nothing; discover_in_place writes in place; none writes guide.yaml."""
import pathlib, types

import yaml

from cryptobench.shared.device.identity import device_id
from cryptobench.stages.discovery import discover
from test_manifest import RUNTIME

STAMP = "20260101T000000Z"
OPTIONS = types.SimpleNamespace(discovery="overwrite", stacktrace=False, stream=False)


def fake_probe(monkeypatch):
    def run(arguments, _stacktrace, _stream=False, *, main_class, **_options):
        assert main_class == "ProbeKt"
        discovery, configured = map(pathlib.Path, arguments.split()[:2])
        capture, trial = discovery / f"probe_{STAMP}.yaml", discovery / f"trial_{STAMP}.yaml"
        capture.write_text(yaml.safe_dump({"schemaVersion": 1, "runtime": RUNTIME, "providers": []}))
        trial.write_text("schemaVersion: 1\n")
        configured.mkdir(parents=True, exist_ok=True)
        (configured / "effective.yaml").write_text("schemaVersion: 1\nproviders: {}\n")
        (configured / "inventory.yaml").write_text("schemaVersion: 1\n")
        return [str(capture), str(trial), str(configured / "effective.yaml")]
    monkeypatch.setattr(discover.gradle_runner, "run", run)


def tree(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def test_discover_published_publishes_under_the_device_id(tmp_path, monkeypatch, capsys):
    fake_probe(monkeypatch)
    root = tmp_path / "results"
    results, found = discover.discover_published(OPTIONS, tmp_path / "global.yaml", None, root, [])
    discovery, effective, capture, trial, files = found.discovery, found.effective, found.capture, found.trial, found.files
    assert results == root / device_id(RUNTIME) and [p.name for p in root.iterdir()] == [device_id(RUNTIME)]
    assert tree(results) == ["configuration/effective.yaml", "configuration/inventory.yaml",
                             f"discovery/probe_{STAMP}.yaml", f"discovery/trial_{STAMP}.yaml"]
    assert list(files) == ["probe", "trial", "inventory", "effective"]
    assert (discovery, effective, capture, trial) == (results / "discovery", results / "configuration/effective.yaml",
                                                      results / f"discovery/probe_{STAMP}.yaml", results / f"discovery/trial_{STAMP}.yaml")
    out = capsys.readouterr().out.splitlines()
    assert out[0] == f"config:    {tmp_path / 'global.yaml'}" and out[-1] == f"results:   {results}"
    assert out[-3] == "effective: 0 entries, 0 skipped" and out[-2].startswith("took:      discover and configure in ")
    wrote = [line.removeprefix("wrote:     ") for line in out if line.startswith("wrote:")]
    assert [pathlib.Path(p).relative_to(root).parts[1:] for p in wrote] == [
        ("discovery", f"probe_{STAMP}.yaml"), ("discovery", f"trial_{STAMP}.yaml"), ("configuration", "effective.yaml")]
    assert all(pathlib.Path(p).relative_to(root).parts[0].startswith(discover.results_layout.STAGING_PREFIX) and not pathlib.Path(p).exists()
               for p in wrote)


def test_discover_staged_leaves_everything_in_the_stage(tmp_path, monkeypatch):
    fake_probe(monkeypatch)
    stage = tmp_path / "stage"
    found = discover.discover_staged(OPTIONS, tmp_path / "global.yaml", None, tmp_path / "root", stage, [])
    discovery, effective, capture, files = found.discovery, found.effective, found.capture, found.files
    assert not (tmp_path / "root").exists() and "guide" not in files
    assert tree(stage) == ["configuration/effective.yaml", "configuration/inventory.yaml",
                           f"discovery/probe_{STAMP}.yaml", f"discovery/trial_{STAMP}.yaml"]
    assert (discovery, effective, capture) == (stage / "discovery", stage / "configuration/effective.yaml", stage / f"discovery/probe_{STAMP}.yaml")


def test_discover_in_place_writes_in_place_and_overwrite_clears_the_old_discovery(tmp_path, monkeypatch):
    fake_probe(monkeypatch)
    (tmp_path / "discovery").mkdir()
    (tmp_path / "discovery/probe_20250101T000000Z.yaml").write_text("{}\n")
    discover.discover_in_place(OPTIONS, tmp_path / "global.yaml", None, tmp_path, [])
    assert tree(tmp_path) == ["configuration/effective.yaml", "configuration/inventory.yaml",
                                               f"discovery/probe_{STAMP}.yaml", f"discovery/trial_{STAMP}.yaml"]
