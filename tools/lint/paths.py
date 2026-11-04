"""Repo paths as the docs graph sees them: which router owns a path, and whether it is a guide, a doc or neither."""
from __future__ import annotations

import posixpath

ROUTERS = ("", "apps/perf-repair")
ENTRY = "AGENTS.md"
GUIDES = {"": "docs/contributing/", "apps/perf-repair": "agents/"}
NOT_GRAPHED = {"apps/benchmark/modules/environment/discovery/docs/tree.md", "apps/benchmark-runner/analysis/tests/golden_summary.md"}


def router_of(path: str) -> str:
    return next((r for r in ROUTERS if r and path.startswith(r + "/")), "")


def local(path: str) -> str:
    r = router_of(path)
    return path[len(r) + 1:] if r else path


def join(base: str, rel: str) -> str:
    return posixpath.normpath(posixpath.join(base, rel)) if base else posixpath.normpath(rel)


def is_guide(path: str) -> bool:
    rel = local(path)
    return rel == ENTRY or rel.startswith(GUIDES[router_of(path)])


def is_doc(path: str) -> bool:
    return not is_guide(path) and "docs" in local(path).split("/")[:-1]


def graphed(path: str) -> bool:
    return path.endswith(".md") and not path.endswith(".system.md") and path not in NOT_GRAPHED \
        and (is_guide(path) or is_doc(path))
