"""Characterization (Py-P5): the one --identify line against golden/identify_device.txt (UPDATE_GOLDEN=1 rewrites it); the harness digest is
normalised, everything else is pinned, so a key added or dropped shows."""
import json, os, pathlib, types

import pipeline
from test_run_inputs import BASE, digests

GOLDEN = pathlib.Path(__file__).with_name("golden") / "identify_device.txt"


class Identified:
    def identity(self):
        return {"sdkInt": 36, "model": "Pixel 10", "fingerprint": "google/pixel/x:17/A/1:user/release-keys"}


def test_today_identify_line_has_no_code_order_or_suppress_errors(tmp_path, monkeypatch, capsys):
    digests(tmp_path)
    monkeypatch.setattr(pipeline.code_digest, "digest", lambda: "<harness digest>")
    pipeline.identify(types.SimpleNamespace(), tmp_path / "global.yaml", Identified())
    line = capsys.readouterr().out.replace(str(tmp_path), "<tmp>")
    if os.environ.get("UPDATE_GOLDEN"):
        GOLDEN.write_text(line)
    assert line == GOLDEN.read_text()
    assert sorted(json.loads(line.split(" ", 1)[1])) == ["config", "deviceId", "harness", "inputs", "mode"]
