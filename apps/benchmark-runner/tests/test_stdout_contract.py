"""The lines perf-repair reads from the runner, printed by the real producers and read by perf-repair's own readers."""
import collections, io, json, re, time, types

import pytest

import failure
import pipeline
from cryptobench.pipeline import took
from cryptobench.shared.log import stdout
from cryptobench.shared.results.manifest import add_to_manifest
from perfrepair.data_handler.outbound import benchmark_runner
from perfrepair.device.delta_estimate import _whole_run_took
from test_manifest import RUNTIME, layout, written
from cryptobench.shared.device.identity import device_id


def streamed(lines):
    process = types.SimpleNamespace(stdout=iter(f"{line}\n" for line in lines))
    return benchmark_runner._stream(process, io.StringIO(), collections.deque(maxlen=40), None)


def test_the_labels_keep_one_column():
    assert {len(label) for label in (stdout.RESULTS, stdout.WROTE, stdout.IDENTITY, stdout.TOOK)} == {11}
    assert stdout.line(stdout.WROTE, "x") == "wrote:     x" and stdout.ERROR == "error: "


def test_failure_prints_the_error_label_without_importing_cryptobench(capsys):
    # dependencies.py reports a missing cryptobench through failure.py, so it keeps its own copy
    with pytest.raises(SystemExit):
        failure.fail("x")
    assert capsys.readouterr().err == stdout.line(stdout.ERROR, "x") + "\n"


def test_last_reads_the_last_labelled_value():
    assert stdout.last(stdout.RESULTS, ["results:   a", "wrote:     b", "results:   c "]) == "c"
    assert stdout.last(stdout.RESULTS, ["wrote:     b"]) is None


def test_took_prints_the_label_and_tenths_of_a_second(capsys):
    took.elapsed("prepare and measure", time.monotonic() - 12.34)
    line = capsys.readouterr().out
    assert re.fullmatch(r"took:      prepare and measure in 12\.[34]s\n", line)
    assert _whole_run_took([line.rstrip("\n")])[0] >= 12.3


def test_the_manifest_write_prints_one_wrote_line_perf_repair_finds(tmp_path, capsys):
    written(tmp_path, "host", layout(tmp_path, measured=False))
    lines = capsys.readouterr().out.splitlines()
    assert lines == [f"wrote:     {tmp_path / 'manifest.yaml'}"]
    assert streamed(lines) == tmp_path / "manifest.yaml"


def test_a_file_added_beside_a_finished_run_reprints_the_manifest_line(tmp_path, capsys):
    written(tmp_path, "host", layout(tmp_path, measured=False))
    (tmp_path / "interop").mkdir()
    (tmp_path / "interop/result.yaml").write_text("{}\n")
    capsys.readouterr()
    add_to_manifest(tmp_path, {"interop": tmp_path / "interop/result.yaml"})
    assert capsys.readouterr().out == f"wrote:     {tmp_path / 'manifest.yaml'}\n"


def test_identify_prints_one_sorted_json_line(tmp_path, monkeypatch, capsys):
    (tmp_path / "global.yaml").write_text("schemaVersion: 1\n")
    monkeypatch.setattr(pipeline, "host_runtime", lambda _options: RUNTIME)
    monkeypatch.setattr(pipeline.code_digest, "digest", lambda: "c" * 64)
    pipeline.identify(types.SimpleNamespace(), tmp_path / "global.yaml", None)
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1 and lines[0].startswith("identity:  {")
    found = json.loads(stdout.last(stdout.IDENTITY, lines))
    assert list(found) == ["code", "config", "deviceId", "harness", "inputs", "mode"] and sorted(found["code"]) == ["runner", "timed"]
    assert found["deviceId"] == device_id(RUNTIME) and found["mode"] == "host" and found["harness"] == "c" * 64
    assert found["config"] == str(tmp_path / "global.yaml") and set(found["inputs"]) == {"bundled", "config"}
    assert lines[0] == "identity:  " + json.dumps(found, sort_keys=True)


def test_identify_on_a_device_reads_getprop_and_says_device(tmp_path, monkeypatch, capsys):
    (tmp_path / "global.yaml").write_text("schemaVersion: 1\n")
    monkeypatch.setattr(pipeline.code_digest, "digest", lambda: "c" * 64)
    pipeline.identify(types.SimpleNamespace(), tmp_path / "global.yaml", types.SimpleNamespace(identity=lambda: RUNTIME))
    found = json.loads(capsys.readouterr().out.removeprefix("identity:  "))
    assert found["mode"] == "device" and found["deviceId"] == device_id(RUNTIME)
