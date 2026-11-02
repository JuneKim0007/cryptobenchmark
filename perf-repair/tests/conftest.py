import os

import pytest

from perfrepair.config import device_results, dotenv, load


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path_factory, monkeypatch):
    """No test reads the developer's .env, perfrepair.yaml or PERFREPAIR_* / ANTHROPIC_* credentials."""
    empty = tmp_path_factory.mktemp("no-settings")
    # every test's folder is a temporary one; test_device_results.py checks the warning itself
    monkeypatch.setattr(device_results, "_warn_if_temp", lambda _folder: None)
    monkeypatch.setattr(dotenv, "ENV_FILE", empty / ".env")
    monkeypatch.setattr(load, "DEFAULT_FILE", empty / "perfrepair.yaml")
    for key in [k for k in os.environ if k.startswith("PERFREPAIR_")] + ["ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"]:
        monkeypatch.delenv(key, raising=False)
