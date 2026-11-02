"""Every setting as one row: its key, chain, check, default and what a bad value does."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from ..catalog.screening import SCREENING
from .check import check_any, check_bool, check_path, check_positive, check_text
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

PATHS_RESULTS = _path("paths.results")
PATHS_PROMPTS = _path("paths.prompts")

SCREENING_CATALOG = _path("device.screening.catalog", invalid=OnInvalid.ERROR, need=Need.DEFAULT, packaged=SCREENING,
                          label="packaged catalog")
SCREENING_AI_REVIEW = Row("device.screening.aiReview", check_bool, default=False)
SCREENING_CLASSIFY = RoleRow("device.screening.classify")
GROUPING_TURNS = Row("device.grouping.turns", check_positive, default=DEFAULT_TURNS)
GROUPING_SESSIONS = Row("device.grouping.sessions", check_positive, default=DEFAULT_SESSIONS)
GROUPING_LIMIT = Row("device.grouping.limit", check_positive)
GROUPING_ASSIGN = RoleRow("device.grouping.assign", {"effort": "low"})
GROUPING_SUPERVISOR = RoleRow("device.grouping.supervisor")
BENCHMARK_CONFIG = _path("device.benchmark.config")
# a bad id must not fall through to another device's numbers
DEVICE_ID = Row("device.id", check_text, invalid=OnInvalid.ERROR)
WORTHINESS = RoleRow("device.worthiness")

APPS_MODE = Row("apps.mode", check_text, default="latency")
APPS_LIMIT = Row("apps.limit", check_positive)
APPS_MEASURE = Row("apps.measure", check_bool, default=False)
APPS_AGENT = RoleRow("apps.agent")
APPS_REPLACE = RoleRow("apps.replace")

ROWS = tuple(v for v in tuple(globals().values()) if isinstance(v, (Row, RoleRow)))


def known_tree() -> dict[str, Any]:
    """Each row's key as nested sections; a leaf holds its OnInvalid; a `<...>` part stands for any key."""
    tree: dict[str, Any] = {}
    for row in ROWS:
        leaves = {row.key: row.invalid} if isinstance(row, Row) else {
            # a role's gateway falling back is the wrong provider, as aiGateway.use is
            f"{row.key}.{k}": AI_GATEWAY_USE.invalid if k == "gateway" else OnInvalid.USE_DEFAULT for k in ROLE_KEYS}
        for key, policy in leaves.items():
            *sections, leaf = key.split(".")
            node = tree
            for part in sections:
                node = node.setdefault(part, {})
            node[leaf] = policy
    return tree
