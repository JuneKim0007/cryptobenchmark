"""#78's vertical scenarios on a fake pipeline: what reruns, what is reused, how many device runs; no model, no device."""
from pathlib import Path

import pytest
import yaml

from perfrepair import run_dir as rd
from perfrepair.catalog.screening import SCREENING
from perfrepair.data_handler.outbound import BenchmarkRunError
from perfrepair.device import stage as device_stage
from perfrepair.device.stage import probe_device
from perfrepair.screen.catalog import load_catalog, screening_catalog

FAKE = Path(__file__).parent / "fixtures" / "device"
ALL_RAN = ["probe", "benchmark", "inbound", "screen"]


@pytest.fixture
def setup(tmp_path):
    config = tmp_path / "global.yaml"
    config.write_text("schemaVersion: 1\nselection: {testSet: x.yaml}\nproviders: {bundled: []}\n")
    return tmp_path / "results", config


def device(root, config, catalog=None, on_device=False):
    lines = []
    done = probe_device(root, catalog or screening_catalog(None), config, on_device, echo=lines.append, benchmark=FAKE)
    return done, [line for line in lines if line.startswith("device ")]


def runs(root):
    log = root / "runs.log"
    return log.read_text().splitlines() if log.is_file() else []


def test_a_fresh_root_runs_every_stage_once_and_records_it(setup):
    root, config = setup
    done, lines = device(root, config)
    assert done.ran == ALL_RAN and len(runs(root)) == 1
    assert lines[0] == "device probe: ran: no manifest.yaml" and lines[-1] == "device screen: ran: probe reruns"
    record, problem = rd.load_device_record(done.folder)
    assert problem is None and record.deviceId == done.folder.name == "fake-api36-00000000"
    assert set(record.inputs) == {"bundled", "config", "names", "screening"} and record.runtime == {"model": "test"}


def test_nothing_changed_reuses_everything_with_no_device_run(setup):
    root, config = setup
    device(root, config)
    before = (root / "fake-api36-00000000" / "grouping" / "items.json").stat().st_mtime_ns
    done, lines = device(root, config)
    assert done.ran == [] and len(runs(root)) == 1
    assert lines == [f"device {s}: reused" for s in ALL_RAN]
    assert (done.folder / "grouping" / "items.json").stat().st_mtime_ns == before


def test_a_provider_added_to_bundled_reruns_the_device_stage_under_the_same_id(setup):
    root, config = setup
    first, _ = device(root, config)
    config.write_text(config.read_text().replace("bundled: []", "bundled: [{artifact: 'g:a:1', create: X}]"))
    done, lines = device(root, config)
    assert done.folder == first.folder and done.ran == ALL_RAN and len(runs(root)) == 2
    assert lines[0] == "device probe: ran: providers.bundled changed"


def test_an_edited_global_yaml_reruns_from_the_probe(setup):
    root, config = setup
    device(root, config)
    config.write_text(config.read_text() + "run: {seed: 7}\n")
    done, lines = device(root, config)
    assert done.ran == ALL_RAN and lines[0] == "device probe: ran: global.yaml changed"


def test_an_edited_screening_catalog_rescreens_only(setup, tmp_path):
    root, config = setup
    device(root, config)
    edited = tmp_path / "screening.yaml"
    edited.write_text(Path(SCREENING).read_text() + "\n# edited\n")
    done, lines = device(root, config, load_catalog(edited))
    assert done.ran == ["screen"] and len(runs(root)) == 1
    assert lines[-1] == "device screen: ran: the screening catalog changed"
    assert yaml.safe_load((done.folder / "device.yaml").read_text())["inputs"]["screening"] == load_catalog(edited).sha256


def test_a_deleted_device_yaml_keeps_the_measured_run_and_redoes_the_rest(setup):
    root, config = setup
    first, _ = device(root, config)
    (first.folder / rd.DEVICE).unlink()
    done, lines = device(root, config)
    assert done.ran == ["inbound", "screen"] and len(runs(root)) == 1
    assert lines[2] == "device inbound: ran: no device.yaml"


def test_measurements_of_an_older_schema_rerun_inbound_without_a_device_run(setup):
    root, config = setup
    first, _ = device(root, config)
    path = first.folder / rd.MEASUREMENTS
    path.write_text(path.read_text().replace('"schemaVersion": 4', '"schemaVersion": 3'))
    done, lines = device(root, config)
    assert done.ran == ["inbound"] and len(runs(root)) == 1
    assert lines[2] == "device inbound: ran: measurements.json unreadable (measurements schemaVersion 3 is not 4)"


def test_a_probe_only_run_is_kept_and_the_benchmark_reuses_its_capture(setup, monkeypatch):
    root, config = setup
    from perfrepair.data_handler.outbound.benchmark_runner import run_pipeline
    run_pipeline(config, root, "configure", benchmark=FAKE, echo=None, extra=("--probe",))
    done, lines = device(root, config)
    assert lines[:2] == ["device probe: reused", "device benchmark: ran: the manifest lists no benchmark"]
    assert runs(root)[-1].endswith("--bench --discovery reuse")


def test_on_a_device_the_benchmark_run_probes_again_and_says_so(setup):
    root, config = setup
    from perfrepair.data_handler.outbound.benchmark_runner import run_pipeline
    run_pipeline(config, root, "device", benchmark=FAKE, echo=None, extra=("--probe",))
    done, lines = device(root, config, on_device=True)
    assert lines[0] == "device probe: ran: a device benchmark probes the device it measures"
    assert "--discovery" not in runs(root)[-1] and runs(root)[-1].endswith("--device")


def test_an_interrupted_benchmark_leaves_no_record_and_the_next_call_runs_it_all(setup, monkeypatch):
    root, config = setup
    first, _ = device(root, config)
    config.write_text(config.read_text().replace("bundled: []", "bundled: [{artifact: 'g:a:1', create: X}]"))
    monkeypatch.setenv("FAKE_INTERRUPT", "1")
    with pytest.raises(BenchmarkRunError):
        device(root, config)
    assert not (first.folder / rd.DEVICE).exists() and not (first.folder / rd.MANIFEST).exists()
    monkeypatch.delenv("FAKE_INTERRUPT")
    done, lines = device(root, config)
    assert done.ran == ALL_RAN and lines[0] == "device probe: ran: no manifest.yaml"


def test_an_interrupted_grouping_build_leaves_no_record_claiming_it(setup, monkeypatch):
    root, config = setup
    first, _ = device(root, config)
    config.write_text(config.read_text().replace("bundled: []", "bundled: [{artifact: 'g:a:1', create: X}]"))

    def lost(*_, **__):
        raise KeyboardInterrupt
    monkeypatch.setattr(device_stage, "build_stage", lost)
    with pytest.raises(KeyboardInterrupt):
        device(root, config)
    assert not (first.folder / rd.DEVICE).exists()
    monkeypatch.undo()
    done, lines = device(root, config)
    assert done.ran == ["inbound", "screen"] and lines[2] == "device inbound: ran: no device.yaml"


def test_a_probe_that_names_another_device_stops(setup, monkeypatch):
    root, config = setup
    real = device_stage.identify
    monkeypatch.setattr(device_stage, "identify", lambda *a: {**real(*a), "deviceId": "other-api36-00000000"})
    with pytest.raises(ValueError, match=r"^device_id_changed: --identify named other-api36-00000000, the probe wrote "
                                         r"fake-api36-00000000$"):
        device(root, config)
