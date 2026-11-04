import logging
import os
from pathlib import Path

import pytest

from perfrepair.catalog.interchange import Interchange
from perfrepair.config import current, device_results, dotenv, load
from perfrepair.grouping import signature
from perfrepair.log.attach import SINK
from perfrepair.stop import policy


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


@pytest.fixture(autouse=True)
def fake_benchmark_root(monkeypatch):
    """The guide reads --identify before its apps; no test reaches the real pipeline, which starts Gradle."""
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(Path(__file__).parent / "fixtures" / "guide"))


@pytest.fixture(autouse=True)
def detached_log():
    """A command's attach() lasts for its process; each test starts without its handlers, level or stops reader."""
    logger = logging.getLogger("perfrepair")
    handlers, level = list(logger.handlers), logger.level
    yield
    policy.reset()
    current.reset()
    SINK.close()
    logger.handlers[:] = handlers
    logger.setLevel(level)


@pytest.fixture
def asked_by_model(monkeypatch):
    """No interchange rule, so every item not screened out is asked: for tests of asking, whatever the fixture's names."""
    monkeypatch.setattr(signature, "interchange", lambda: Interchange({}, frozenset(), ()))
