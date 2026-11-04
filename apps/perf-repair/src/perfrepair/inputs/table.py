"""Every setting as one row: its key, chain, check, default and what a bad value does."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from ..catalog.screening import SCREENING
from ..dto.benchmark_coverage import GAP_DELTA, ON_GAP, ON_SETUP_MISMATCH, SETUP_STOP
from ..dto.bundled import OFF, ON_MISSING, WARN
from ..dto.change import DROP_IN
from ..dto.perf_mode import GENERIC
from ..stop.codes import CODES_LIST, OVERRIDABLE
from .check import (
    check_any,
    check_bool,
    check_from_apps,
    check_max_change,
    check_one_of,
    check_path,
    check_perf_mode,
    check_positive,
    check_targets,
    check_text,
)
from .resolve import Candidate, Need, OnInvalid, Resolved, resolve


class Layer(Enum):
    CLI = "cli"
    FILE = "file"
    ROLE = "the role's section"
    ENV = "environment"
    BLOCK = "the gateway's block"
    DOTENV = ".env"
    ROLE_DEFAULT = "the role's code default"
    DEFAULT = "code default"


FILE_CHAIN = (Layer.CLI, Layer.FILE, Layer.DEFAULT)
GATEWAY_CHAIN = (Layer.CLI, Layer.ROLE, Layer.ENV, Layer.BLOCK, Layer.DOTENV, Layer.ROLE_DEFAULT, Layer.DEFAULT)
ROLE_KEYS = ("gateway", "model", "effort")
DEFAULT_TURNS, DEFAULT_SESSIONS = 3, 2


@dataclass(frozen=True)
class Row:
    key: str
    check: Callable[[str, Any], None] = check_any
    default: Any = None
    invalid: OnInvalid = OnInvalid.USE_DEFAULT
    chain: tuple[Layer, ...] = FILE_CHAIN
    path: bool = False
    need: Need = Need.OPTIONAL
    packaged: Path | None = None
    label: str = "packaged default"

    def resolve(self, explicit: Iterable[Candidate], load: Callable[[Any], Any], note: str = "") -> Resolved:
        default = [Candidate(self.packaged, self.label, explicit=False, note=note)] if self.packaged else []
        return resolve(self.key, [*explicit, *default], load, self.need)


@dataclass(frozen=True)
class RoleRow:
    """A role's section; its keys are ROLE_KEYS, ranked by GATEWAY_CHAIN and checked by the gateway at spawn."""
    key: str
    defaults: Mapping[str, str] = field(default_factory=dict)


def _path(key: str, **kwargs: Any) -> Row:
    return Row(key, check_path, path=True, **kwargs)


# gateways sit above this layer: a gateway's name and its block's values are checked at spawn
AI_GATEWAY_USE = Row("aiGateway.use", check_text, invalid=OnInvalid.ERROR, chain=GATEWAY_CHAIN)
AI_GATEWAY_AUTH = Row("aiGateway.<gateway>.auth", invalid=OnInvalid.ERROR, chain=GATEWAY_CHAIN)
AI_GATEWAY_KEY = Row("aiGateway.<gateway>.<key>", chain=GATEWAY_CHAIN)

PATHS_PROMPTS = _path("paths.prompts")

SCREENING_CATALOG = _path("device.screening.catalog", invalid=OnInvalid.ERROR, need=Need.DEFAULT, packaged=SCREENING,
                          label="packaged catalog")
SCREENING_AI_REVIEW = Row("device.screening.aiReview", check_bool, default=False)
SCREENING_CLASSIFY = RoleRow("device.screening.classify")
GROUPING_TURNS = Row("device.grouping.turns", check_positive, default=DEFAULT_TURNS)
GROUPING_SESSIONS = Row("device.grouping.sessions", check_positive, default=DEFAULT_SESSIONS)
GROUPING_LIMIT = Row("device.grouping.limit", check_positive)
# knowledge that is missing is asked either way, so a bad value is never unsafe
GROUPING_NO_RERUN = Row("device.grouping.noRerun", check_bool, default=True)
GROUPING_ASSIGN = RoleRow("device.grouping.assign", {"effort": "low"})
GROUPING_SUPERVISOR = RoleRow("device.grouping.supervisor")
# a gap the gate finds: measured in one delta, or a stop; a setup that differs never starts a whole rerun unless named
BENCHMARK_ON_GAP = Row("device.benchmark.onGap", partial(check_one_of, choices=ON_GAP), default=GAP_DELTA)
BENCHMARK_ON_SETUP_MISMATCH = Row("device.benchmark.onSetupMismatch", partial(check_one_of, choices=ON_SETUP_MISMATCH),
                                  default=SETUP_STOP)
# off is a full-device run: more device time and model calls, never a wrong result
FILTER_BY_APPS = Row("device.filterByApps", check_bool, default=True)
BUNDLED_ON_MISSING = Row("device.bundled.onMissing", partial(check_one_of, choices=ON_MISSING), default=WARN)
# apply builds catalog rows into the harness unreviewed, so a bad value falls back to off
BUNDLED_FROM_APPS = Row("device.bundled.fromApps", check_from_apps, default=OFF)
# a bad id must not fall through to another device's numbers
DEVICE_ID = Row("device.id", check_text, invalid=OnInvalid.ERROR)
WORTHINESS = RoleRow("device.worthiness")

APPS_TARGETS = Row("apps.targets", check_targets)
APPS_PERF_MODE = Row("apps.perfMode", check_perf_mode, default=GENERIC)
APPS_LIMIT = Row("apps.limit", check_positive)
APPS_MEASURE = Row("apps.measure", check_bool, default=False)
# the highest change class the guide may apply; a bad value falls back to drop-in, the class that changes no contract
APPS_MAX_CHANGE = Row("apps.maxChange", check_max_change, default=DROP_IN)
APPS_AGENT = RoleRow("apps.agent")
APPS_REPLACE = RoleRow("apps.replace")

# seconds before a hung child is killed; a device benchmark call runs for hours, a model call for minutes
TIMEOUT_CLAUDE = Row("timeouts.claude", check_positive, default=3600)
TIMEOUT_PIPELINE = Row("timeouts.pipeline", check_positive, default=86400)

# stops.<code>: an overridable code's action; a bad value warns and keeps the code's default
STOP_ROWS = {c.code: Row(f"stops.{c.code}", partial(check_one_of, choices=c.allowed), default=c.action) for c in OVERRIDABLE}
# a fixed code is known, so setting it warns where it fires instead of as an unknown key
FIXED_STOP_KEYS = tuple(f"stops.{c.code}" for c in CODES_LIST if c.fixed)

ROWS = (*(v for v in tuple(globals().values()) if isinstance(v, (Row, RoleRow))), *STOP_ROWS.values())


def known_tree() -> dict[str, Any]:
    """Each row's key as nested sections; a leaf holds its OnInvalid; a `<...>` part stands for any key."""
    tree: dict[str, Any] = {}
    for row in ROWS:
        leaves = {row.key: row.invalid} if isinstance(row, Row) else {
            # a role's gateway falling back is the wrong provider, as aiGateway.use is
            f"{row.key}.{k}": AI_GATEWAY_USE.invalid if k == "gateway" else OnInvalid.USE_DEFAULT for k in ROLE_KEYS}
        for key, policy in leaves.items():
            _leaf(tree, key, policy)
    for key in FIXED_STOP_KEYS:
        _leaf(tree, key, OnInvalid.USE_DEFAULT)
    return tree


def _leaf(tree: dict[str, Any], key: str, policy: OnInvalid) -> None:
    *sections, leaf = key.split(".")
    node = tree
    for part in sections:
        node = node.setdefault(part, {})
    node[leaf] = policy
