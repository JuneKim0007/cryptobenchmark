import os
from pathlib import Path

from perfrepair.config.dotenv import ROOT, load_env


def test_env_file_fills_unset_keys_and_keeps_its_own_keys_out_of_the_environment(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("# comment\nPERFREPAIR_AGENT=claude\nPERFREPAIR_MODEL='m'\nOTHER_KEY=x\nSET_KEY=file\nEMPTY=\n")
    monkeypatch.delenv("OTHER_KEY", raising=False)
    monkeypatch.delenv("EMPTY", raising=False)
    monkeypatch.setenv("SET_KEY", "env")
    values = load_env(f)
    assert values == {"PERFREPAIR_AGENT": "claude", "PERFREPAIR_MODEL": "m", "OTHER_KEY": "x", "SET_KEY": "file"}
    assert os.environ["OTHER_KEY"] == "x" and os.environ["SET_KEY"] == "env" and "EMPTY" not in os.environ
    assert "PERFREPAIR_AGENT" not in os.environ


def test_env_root_is_the_perf_repair_folder():
    assert ROOT == Path(__file__).resolve().parents[1] and (ROOT / ".env.example").is_file()
