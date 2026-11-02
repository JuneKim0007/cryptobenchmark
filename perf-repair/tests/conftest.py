import os

import pytest

from perfrepair.config import dotenv, load


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path_factory, monkeypatch):
    """No test reads the developer's .env, perfrepair.yaml or PERFREPAIR_* / ANTHROPIC_API_KEY."""
    empty = tmp_path_factory.mktemp("no-settings")
    monkeypatch.setattr(dotenv, "ENV_FILE", empty / ".env")
    monkeypatch.setattr(load, "DEFAULT_FILE", empty / "perfrepair.yaml")
    for key in [k for k in os.environ if k.startswith("PERFREPAIR_")] + ["ANTHROPIC_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
