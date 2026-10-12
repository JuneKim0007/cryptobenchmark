import os

from perfrepair.env import load_env


def test_env_file_fills_only_unset_keys(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("# comment\nPERFREPAIR_AGENT=claude\nPERFREPAIR_MODEL='m'\nANTHROPIC_API_KEY=\nPERFREPAIR_EFFORT=high\n")
    monkeypatch.delenv("PERFREPAIR_AGENT", raising=False)
    monkeypatch.delenv("PERFREPAIR_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("PERFREPAIR_EFFORT", "low")
    load_env(f)
    assert os.environ["PERFREPAIR_AGENT"] == "claude" and os.environ["PERFREPAIR_MODEL"] == "m"
    assert "ANTHROPIC_API_KEY" not in os.environ and os.environ["PERFREPAIR_EFFORT"] == "low"
