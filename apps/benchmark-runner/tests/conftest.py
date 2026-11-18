import pytest


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path_factory, monkeypatch):
    """The phone locks a run takes land in a temporary user cache, never the developer's."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path_factory.mktemp("cache")))
