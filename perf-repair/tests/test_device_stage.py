"""#78's vertical scenarios on a fake pipeline: what reruns, what is reused, how many device runs; no model, no device."""
from pathlib import Path

import pytest
import yaml

from perfrepair import run_dir as rd
from perfrepair.catalog.screening import SCREENING
from perfrepair.check.run import validate_run
from perfrepair.device import stage as device_stage
from perfrepair.device.measures import switched_on
from perfrepair.device.stage import DEVICE_PROBES, probe_device
from perfrepair.dto.event import END
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.screen.catalog import load_catalog, screening_catalog
from perfrepair.config.load import load
from perfrepair.config.stops import install_stops
from perfrepair.stop import Halt
from helpers import TIMING, captured_events

FAKE = Path(__file__).parent / "fixtures" / "device"
ALL_RAN = ["probe", "benchmark", "inbound", "screen", "primitives"]


@pytest.fixture
def setup(tmp_path):
    config = tmp_path / "global.yaml"
    config.write_text("schemaVersion: 1\nselection: {testSet: x.yaml}\nproviders: {bundled: []}\n")
    return tmp_path / "results", config


def device(root, config, catalog=None, on_device=False, refresh=False):
    lines = []
    done = probe_device(root, catalog or screening_catalog(None), config, on_device, echo=lines.append, benchmark=FAKE, perf=TIMING,
                        refresh=refresh)
    return done, [line for line in lines if line.startswith("device ")]


def runs(root):
    log = root / "runs.log"
    return log.read_text().splitlines() if log.is_file() else []


def test_a_fresh_root_runs_every_stage_once_and_records_it(setup):
    root, config = setup
    done, lines = device(root, config)
    assert done.ran == ALL_RAN and len(runs(root)) == 1
    assert lines[0] == "device probe: ran: no manifest.yaml" and lines[-2] == "device screen: ran: probe reruns"
    assert lines[-1] == "device primitives: ran: inbound reruns"
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


def test_the_primitives_table_is_written_and_recorded_with_its_input_digests(setup):
    root, config = setup
    done, _ = device(root, config)
    record, _ = rd.load_device_record(done.folder)
    assert (done.folder / rd.PRIMITIVES).read_text().startswith("#schemaVersion\t2\ntype\talgorithm\t")
    assert set(record.primitives) == {"rows", "measurements", "screen"} and all(record.primitives.values())


def test_a_hand_edited_measurements_json_rebuilds_only_the_table(setup):
    root, config = setup
    first, _ = device(root, config)
    path = first.folder / rd.MEASUREMENTS
    path.write_text(path.read_text().replace('"comparability": [', '"comparability": ["edited", ', 1))
    done, lines = device(root, config)
    assert done.ran == ["primitives"] and lines[-1] == "device primitives: ran: measurements.json changed"


def test_refresh_rebuilds_only_the_table_and_a_record_without_its_digests_does_too(setup):
    root, config = setup
    first, _ = device(root, config)
    done, lines = device(root, config, refresh=True)
    assert done.ran == ["primitives"] and lines[-1] == "device primitives: ran: --refresh" and len(runs(root)) == 1
    record = yaml.safe_load((first.folder / rd.DEVICE).read_text())
    del record["primitives"]
    (first.folder / rd.DEVICE).write_text(yaml.safe_dump(record))
    done, lines = device(root, config)
    assert done.ran == ["primitives"] and lines[-1] == "device primitives: ran: device.yaml records no primitives.tsv inputs"


def test_the_folder_validator_checks_the_table_against_its_inputs(setup):
    root, config = setup
    first, _ = device(root, config)
    assert validate_run(first.folder, screening_catalog(None))[rd.PRIMITIVES] == []
    path = first.folder / rd.PRIMITIVES
    lines = path.read_text().splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n")
    assert validate_run(first.folder, screening_catalog(None))[rd.PRIMITIVES][0].endswith(": missing")


def test_a_deleted_table_is_rebuilt_alone(setup):
    root, config = setup
    first, _ = device(root, config)
    (first.folder / rd.PRIMITIVES).unlink()
    done, lines = device(root, config)
    assert done.ran == ["primitives"] and lines[-1] == "device primitives: ran: primitives.tsv missing"


def test_a_table_in_an_older_schema_is_rebuilt_alone(setup):
    root, config = setup
    first, _ = device(root, config)
    path = first.folder / rd.PRIMITIVES
    path.write_text(path.read_text().replace("#schemaVersion\t2", "#schemaVersion\t1", 1))
    done, lines = device(root, config)
    assert done.ran == ["primitives"] and lines[-1].startswith("device primitives: ran: primitives.tsv starts '#schemaVersion")


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
    assert done.ran == ["screen", "primitives"] and len(runs(root)) == 1
    assert lines[-2] == "device screen: ran: the screening catalog changed"
    assert yaml.safe_load((done.folder / "device.yaml").read_text())["inputs"]["screening"] == load_catalog(edited).sha256


def test_a_deleted_device_yaml_keeps_the_measured_run_and_redoes_the_rest(setup):
    root, config = setup
    first, _ = device(root, config)
    (first.folder / rd.DEVICE).unlink()
    done, lines = device(root, config)
    assert done.ran == ["inbound", "screen", "primitives"] and len(runs(root)) == 1
    assert lines[2] == "device inbound: ran: no device.yaml"


def test_measurements_of_an_older_schema_rerun_inbound_without_a_device_run(setup):
    root, config = setup
    first, _ = device(root, config)
    path = first.folder / rd.MEASUREMENTS
    path.write_text(path.read_text().replace('"schemaVersion": 4', '"schemaVersion": 3'))
    done, lines = device(root, config)
    assert done.ran == ["inbound", "primitives"] and len(runs(root)) == 1
    assert lines[2] == "device inbound: ran: measurements.json unreadable (measurements schemaVersion 3 is not 4)"


def test_a_probe_only_run_is_kept_and_the_benchmark_reuses_its_capture(setup, monkeypatch):
    root, config = setup
    from perfrepair.data_handler.outbound.benchmark_runner import run_pipeline
    run_pipeline(config, root, "configure", benchmark=FAKE, echo=None, extra=("--probe",), device=root)
    done, lines = device(root, config)
    assert lines[:2] == ["device probe: reused", "device benchmark: ran: the manifest lists no benchmark"]
    assert runs(root)[-1].endswith("--bench --discovery reuse")


def test_on_a_device_the_benchmark_run_probes_again_and_says_so(setup):
    root, config = setup
    from perfrepair.data_handler.outbound.benchmark_runner import run_pipeline
    run_pipeline(config, root, "device", benchmark=FAKE, echo=None, extra=("--probe",), device=root)
    done, lines = device(root, config, on_device=True)
    assert lines[0] == "device probe: ran: a device benchmark probes the device it measures"
    assert "--discovery" not in runs(root)[-1] and runs(root)[-1].endswith("--device")


@pytest.mark.parametrize("detect, ran_with", [(None, [("ran", DEVICE_PROBES)]), (lambda _: [], [])], ids=["whole", "scoped"])
def test_on_a_device_only_a_whole_run_reports_the_probe_as_ran_with_the_benchmark(setup, detect, ran_with):
    root, config = setup
    from perfrepair.data_handler.outbound.benchmark_runner import run_pipeline
    run_pipeline(config, root, "device", benchmark=FAKE, echo=None, extra=("--probe",), device=root)
    with captured_events() as events:
        probe_device(root, screening_catalog(None), config, True, echo=lambda _: None, benchmark=FAKE, detect=detect, perf=TIMING)
    assert [(e.outcome, e.detail) for e in events
            if (e.step, e.event, e.data.get("ranWith")) == ("probe", END, "benchmark")] == ran_with


def test_an_interrupted_benchmark_leaves_no_record_and_the_next_call_runs_it_all(setup, monkeypatch):
    root, config = setup
    first, _ = device(root, config)
    config.write_text(config.read_text().replace("bundled: []", "bundled: [{artifact: 'g:a:1', create: X}]"))
    monkeypatch.setenv("FAKE_INTERRUPT", "1")
    with pytest.raises(Halt, match="^pipeline_failed: "):
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
    assert done.ran == ["inbound", "screen", "primitives"] and lines[2] == "device inbound: ran: no device.yaml"


def test_a_probe_that_names_another_device_stops(setup, monkeypatch):
    root, config = setup
    real = device_stage.identify
    monkeypatch.setattr(device_stage, "identify", lambda *a: {**real(*a), "deviceId": "other-api36-00000000"})
    with pytest.raises(ValueError, match=r"^device_id_changed: --identify named other-api36-00000000, the probe wrote "
                                         r"fake-api36-00000000$"):
        device(root, config)


def _with_run(config, run):
    config.write_text("schemaVersion: 1\nselection: {testSet: x.yaml}\nproviders: {bundled: []}\n" + run)
    return config


def test_a_selected_metric_the_config_cannot_measure_stops_before_any_device_run(setup):
    root, config = setup
    with pytest.raises(Halt, match="perf_mode_unmeasured: perfMode latency\\+memAlloc selects allocationCount"):
        probe_device(root, screening_catalog(None), config, echo=lambda _: None, benchmark=FAKE,
                     perf=PerfMode.parse(["latency", "memAlloc"]))
    assert runs(root) == []


def test_generic_is_checked_like_a_list_so_missing_allocation_stops(setup):
    root, config = setup
    with pytest.raises(Halt, match="perf_mode_unmeasured: perfMode generic selects allocationCount"):
        probe_device(root, screening_catalog(None), config, echo=lambda _: None, benchmark=FAKE, perf=PerfMode.parse("generic"))
    assert runs(root) == []


def test_stops_warn_turns_perf_mode_unmeasured_into_a_warning_and_the_device_stage_runs(setup, tmp_path):
    root, config = setup
    (tmp_path / "perfrepair.yaml").write_text("stops: {perf_mode_unmeasured: warn}\n")
    install_stops(load(tmp_path / "perfrepair.yaml", {}, {}))
    with captured_events() as events:
        probe_device(root, screening_catalog(None), config, echo=lambda _: None, benchmark=FAKE,
                     perf=PerfMode.parse(["latency", "memAlloc"]))
    warned = [e for e in events if e.data.get("code") == "perf_mode_unmeasured"]
    assert [e.outcome for e in warned] == ["warn"] and runs(root)


def test_unselected_measurements_and_run_level_energy_are_logged_not_refused(setup, caplog):
    root, config = setup
    _with_run(config, "run: {metrics: [TIME, ALLOCATION]}\n")
    with caplog.at_level("INFO", logger="perfrepair.event"):
        probe_device(root, screening_catalog(None), config, echo=lambda _: None, benchmark=FAKE,
                     perf=PerfMode.parse(["energy", "latency"]))
    text = caplog.text
    assert "energyJ is selected but" in text and "perf_mode_extra:" in text and "allocationCount" in text
    assert switched_on({"run": {"metrics": ["TIME"], "harness": {"energy": {"capture": "measured"}}}}) == {"TIME", "energy"}
