"""#78's vertical scenarios on a fake pipeline: what reruns, what is reused, how many device runs; no model, no device."""
from pathlib import Path

import pytest
import yaml

from perfrepair import run_dir as rd
from perfrepair.catalog.screening import SCREENING
from perfrepair.check.run import validate_run
from perfrepair.device import stage as device_stage, stage_run
from perfrepair.device.measures import switched_on
from perfrepair.device.stage_pass import DEVICE_PROBES
from perfrepair.device.stage import probe_device
from perfrepair.dto.event import END
from perfrepair.dto.metrics import TIME
from perfrepair.run_dir import METRICS_CONFIG
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
    assert (done.folder / rd.PRIMITIVES).read_text().startswith("#schemaVersion\t3\ntype\talgorithm\t")
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
    path.write_text(path.read_text().replace("#schemaVersion\t3", "#schemaVersion\t2", 1))
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
    monkeypatch.setattr(stage_run, "build_stage", lost)
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


def _probe(root, config, perf, on_device=False):
    lines = []
    made = probe_device(root, screening_catalog(None), config, on_device, echo=lines.append, benchmark=FAKE,
                        perf=PerfMode.parse(perf))
    return made, lines


def _measured_metrics(made):
    generated = made.folder / METRICS_CONFIG
    return yaml.safe_load(generated.read_text())["run"]["metrics"] if generated.is_file() else None


def test_generic_on_a_host_measures_time_and_never_stops_and_the_config_keeps_its_digest(setup):
    root, config = setup
    made, lines = _probe(root, config, "generic")
    assert _measured_metrics(made) is None and made.config == config.resolve()
    assert any(line.startswith("measures: timeNs on the host JVM harness") and
               "not measured: allocationCount, energyJ" in line for line in lines)


def test_generic_on_a_device_measures_time_and_allocation_through_a_generated_config(setup):
    root, config = setup
    made, lines = _probe(root, config, "generic", on_device=True)
    assert _measured_metrics(made) == ["TIME", "ALLOCATION"]
    assert any("timeNs, allocationCount on the device harness" in line and "not measured: energyJ" in line for line in lines)


def test_a_generated_config_is_the_base_of_the_next_run_so_nothing_reruns(setup):
    root, config = setup
    _probe(root, config, "generic", on_device=True)
    made, _ = _probe(root, config, "generic", on_device=True)
    assert made.ran == []


def test_a_perf_mode_that_changes_what_is_measured_reruns_the_benchmark(setup):
    root, config = setup
    _probe(root, config, ["latency"], on_device=True)
    made, _ = _probe(root, config, "generic", on_device=True)
    assert "benchmark" in made.ran


def test_generic_with_no_energy_capture_fires_no_code_whatever_stops_says(setup, tmp_path):
    root, config = setup
    (tmp_path / "perfrepair.yaml").write_text("stops: {perf_mode_maybe_unmeasured: stop, perf_mode_unmeasured: stop}\n")
    install_stops(load(tmp_path / "perfrepair.yaml", {}, {}))
    with captured_events() as events:
        _probe(root, config, "generic", on_device=True)
    assert not [e for e in events if str(e.data.get("code")).startswith("perf_mode")]


@pytest.mark.parametrize("perf, metric", [(["energy"], "energyJ"), (["latency", "memAlloc"], "allocationCount")])
def test_a_strict_metric_the_host_cannot_measure_stops_and_names_the_harness(setup, perf, metric):
    root, config = setup
    with pytest.raises(Halt) as stopped:
        _probe(root, config, perf)
    assert stopped.value.code == "perf_mode_unmeasured"
    assert metric in stopped.value.detail and "host JVM harness" in stopped.value.detail
    assert "run.metrics" not in stopped.value.detail and "run.metrics" not in stopped.value.next_step
    assert runs(root) == []


def test_a_strict_allocation_on_a_device_is_measured_not_stopped(setup):
    root, config = setup
    made, _ = _probe(root, config, ["memAlloc"], on_device=True)
    assert _measured_metrics(made) == ["TIME", "ALLOCATION"]


def test_stops_warn_turns_perf_mode_unmeasured_into_a_warning_and_the_device_stage_runs(setup, tmp_path):
    root, config = setup
    (tmp_path / "perfrepair.yaml").write_text("stops: {perf_mode_unmeasured: warn}\n")
    install_stops(load(tmp_path / "perfrepair.yaml", {}, {}))
    with captured_events() as events:
        _probe(root, config, ["latency", "memAlloc"])
    warned = [e for e in events if e.data.get("code") == "perf_mode_unmeasured"]
    assert [e.outcome for e in warned] == ["warn"] and runs(root)


def test_a_differing_user_run_metrics_warns_once_and_perf_mode_wins(setup):
    root, config = setup
    _with_run(config, "run: {metrics: [TIME, ALLOCATION]}\n")
    with captured_events() as events:
        made, _ = _probe(root, config, "generic")
    warned = [e for e in events if e.data.get("code") == "run_metrics_overridden"]
    assert [e.outcome for e in warned] == ["warn"] and "['TIME', 'ALLOCATION']" in warned[0].detail
    assert _measured_metrics(made) == ["TIME"]


def test_a_user_run_metrics_that_matches_is_silent_and_rewrites_nothing(setup):
    root, config = setup
    _with_run(config, "run: {metrics: [ALLOCATION, TIME]}\n")
    with captured_events() as events:
        made, _ = _probe(root, config, "generic", on_device=True)
    assert not [e for e in events if e.data.get("code") == "run_metrics_overridden"] and _measured_metrics(made) is None


def test_what_the_config_would_refuse_beside_the_metrics_goes_too(setup, tmp_path):
    root, config = setup
    _with_run(config, "run: {metrics: [TIME, ALLOCATION], passes: {timing: {samples: 3}, allocation: {samples: 2}}, "
                      "harness: {energy: {capture: measured}}}\n")
    made, _ = _probe(root, config, "generic")
    run = yaml.safe_load((made.folder / METRICS_CONFIG).read_text())["run"]
    assert run["metrics"] == ["TIME"] and list(run["passes"]) == ["timing"] and run["harness"]["energy"]["capture"] == "none"


def test_several_apps_only_a_strict_one_makes_a_metric_required(setup):
    root, config = setup
    both = PerfMode.union([PerfMode.parse("generic"), PerfMode.parse(["latency"])])
    made = probe_device(root, screening_catalog(None), config, echo=lambda _: None, benchmark=FAKE, perf=both, required=(TIME,))
    assert _measured_metrics(made) is None


def test_a_missing_module_stops_before_any_pipeline_run(setup, monkeypatch):
    root, config = setup
    monkeypatch.setenv("FAKE_MISSING_DEPENDENCY", "matplotlib")
    with pytest.raises(Halt) as stopped:
        _probe(root, config, "generic")
    assert stopped.value.code == "missing_dependency" and stopped.value.detail == "matplotlib; pip install -r requirements.txt"
    assert runs(root) == []


def test_unselected_measurements_and_run_level_energy_are_logged_not_refused(setup, caplog):
    root, config = setup
    with caplog.at_level("INFO", logger="perfrepair.event"):
        _probe(root, config, ["energy", "latency"], on_device=True)
    assert "energyJ is selected but" in caplog.text
    _with_run(config, "run: {harness: {energy: {capture: measured}}}\n")
    caplog.clear()
    with caplog.at_level("INFO", logger="perfrepair.event"):
        _probe(root, config, ["latency"], on_device=True)
    assert "perf_mode_extra:" in caplog.text and "energyJ" in caplog.text
    assert switched_on({"run": {"metrics": ["TIME"], "harness": {"energy": {"capture": "measured"}}}}) == {"TIME", "energy"}
