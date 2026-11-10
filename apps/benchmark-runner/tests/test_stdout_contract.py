"""The lines perf-repair reads from the runner, printed by the real producers and matched by perf-repair's own regexes."""
import ast, json, pathlib, re, time, types

import pipeline
from stages import took
from results.manifest import add_to_manifest
from test_manifest import RUNTIME, layout, written
from device.identity import device_id

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUTBOUND = ROOT / "apps/perf-repair/src/perfrepair/data_handler/outbound/benchmark_runner.py"
DELTA_ESTIMATE = ROOT / "apps/perf-repair/src/perfrepair/device/delta_estimate.py"


def compiled(path, name):
    """The pattern perf-repair compiles under `name`, read from its source so the two ends cannot drift apart."""
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and [getattr(t, "id", None) for t in node.targets] == [name]:
            return re.compile(node.value.args[0].value)
    raise AssertionError(f"{name} not in {path}")


def test_perf_repairs_patterns_are_the_ones_pinned_here():
    assert compiled(OUTBOUND, "WROTE_MANIFEST").pattern == r"^wrote:\s+(.*/manifest\.yaml)$"
    assert compiled(OUTBOUND, "IDENTITY").pattern == r"^identity:\s+(\{.*\})$"
    assert compiled(DELTA_ESTIMATE, "TOOK").pattern == r"^took:\s+prepare and measure in (?P<s>[0-9.]+)s$"


def test_took_prints_the_label_and_tenths_of_a_second(capsys):
    took.elapsed("prepare and measure", time.monotonic() - 12.34)
    line = capsys.readouterr().out
    assert re.fullmatch(r"took:      prepare and measure in 12\.[34]s\n", line)
    assert float(compiled(DELTA_ESTIMATE, "TOOK").match(line.rstrip("\n")).group("s")) >= 12.3


def test_the_manifest_write_prints_one_wrote_line_perf_repair_finds(tmp_path, capsys):
    written(tmp_path, "host", layout(tmp_path, measured=False))
    lines = capsys.readouterr().out.splitlines()
    assert lines == [f"wrote:     {tmp_path / 'manifest.yaml'}"]
    assert compiled(OUTBOUND, "WROTE_MANIFEST").match(lines[-1]).group(1) == str(tmp_path / "manifest.yaml")


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
    found = json.loads(compiled(OUTBOUND, "IDENTITY").match(lines[0]).group(1))
    assert list(found) == ["config", "deviceId", "harness", "inputs", "mode"]
    assert found["deviceId"] == device_id(RUNTIME) and found["mode"] == "host" and found["harness"] == "c" * 64
    assert found["config"] == str(tmp_path / "global.yaml") and set(found["inputs"]) == {"bundled", "config"}
    assert lines[0] == "identity:  " + json.dumps(found, sort_keys=True)


def test_identify_on_a_device_reads_getprop_and_says_device(tmp_path, monkeypatch, capsys):
    (tmp_path / "global.yaml").write_text("schemaVersion: 1\n")
    monkeypatch.setattr(pipeline.code_digest, "digest", lambda: "c" * 64)
    pipeline.identify(types.SimpleNamespace(), tmp_path / "global.yaml", types.SimpleNamespace(identity=lambda: RUNTIME))
    found = json.loads(capsys.readouterr().out.removeprefix("identity:  "))
    assert found["mode"] == "device" and found["deviceId"] == device_id(RUNTIME)
