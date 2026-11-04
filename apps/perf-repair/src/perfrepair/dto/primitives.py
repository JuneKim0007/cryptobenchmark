"""primitives.tsv: one line per measured primitive, a median column per (metric, input size), n and cv per metric."""
from __future__ import annotations

from dataclasses import dataclass

# 3: a variant column; a line per variant, never mixed
SCHEMA_VERSION = 3
SCHEMA_LINE = f"#schemaVersion\t{SCHEMA_VERSION}"
KEY = ("type", "algorithm", "provider", "operation", "keySize", "phase", "variant", "status")
ABSENT = "-"
SIGNIFICANT = 4


def rounded(x: float | None) -> float | None:
    """The table is a view for reading; statistics stay in measurements.json, so 4 significant digits suffice."""
    return None if x is None else float(f"{x:.{SIGNIFICANT}g}")


def column(metric: str, input_size: int | None) -> str:
    return f"{metric}@{ABSENT if input_size is None else input_size}"


def cv_column(metric: str) -> str:
    return f"{metric}.cv"


def n_column(metric: str) -> str:
    return f"{metric}.n"


def _text(x) -> str:
    if x is None:
        return ABSENT
    if isinstance(x, float):
        if x == 0 or 1e-3 <= abs(x) < 1e15:
            return f"{x:f}".rstrip("0").rstrip(".")
        return f"{x:.{SIGNIFICANT}g}"
    return str(x)


def _number(text: str) -> float | None:
    return None if text == ABSENT else float(text)


def _count(text: str) -> int | None:
    return None if text == ABSENT else int(text)


def _header(names: list[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """The median columns and the metrics: the key, `<metric>@<size>` columns, then `<metric>.n` and `<metric>.cv`."""
    if tuple(names[:len(KEY)]) != KEY:
        raise ValueError(f"primitives.tsv header starts {names[:len(KEY)]}, not {list(KEY)}")
    n_at = len(KEY) + sum(1 for c in names[len(KEY):] if "@" in c)
    cv_at = n_at + (len(names) - n_at) // 2
    metrics = tuple(c.removesuffix(".n") for c in names[n_at:cv_at])
    if names[n_at:] != [*map(n_column, metrics), *map(cv_column, metrics)]:
        raise ValueError(f"primitives.tsv header after the medians {names[n_at:]} is not <metric>.n then <metric>.cv")
    return tuple(names[len(KEY):n_at]), metrics


@dataclass(frozen=True)
class PrimitiveLine:
    type: str
    algorithm: str
    provider: str
    operation: str
    keySize: int | None
    phase: str | None
    variant: str
    status: str
    medians: dict[str, float | None]
    # runs per metric: one energy window is not fifty timings
    n: dict[str, int | None]
    cv: dict[str, float | None]

    @property
    def key(self) -> tuple:
        return tuple(getattr(self, f) for f in KEY)


@dataclass(frozen=True)
class PrimitivesTable:
    columns: tuple[str, ...]
    metrics: tuple[str, ...]
    lines: tuple[PrimitiveLine, ...]

    @property
    def header(self) -> tuple[str, ...]:
        return (*KEY, *self.columns, *(n_column(m) for m in self.metrics), *(cv_column(m) for m in self.metrics))

    def to_tsv(self) -> str:
        out = [SCHEMA_LINE, "\t".join(self.header)]
        for line in self.lines:
            cells = [*line.key, *(line.medians.get(c) for c in self.columns), *(line.n.get(m) for m in self.metrics),
                     *(line.cv.get(m) for m in self.metrics)]
            out.append("\t".join(_text(c) for c in cells))
        return "\n".join(out) + "\n"

    @classmethod
    def from_tsv(cls, text: str) -> "PrimitivesTable":
        first, header, *body = text.rstrip("\n").split("\n")
        if first != SCHEMA_LINE:
            raise ValueError(f"primitives.tsv first line {first!r} is not {SCHEMA_LINE!r}")
        names = header.split("\t")
        columns, metrics = _header(names)
        n_at, cv_at = len(KEY) + len(columns), len(KEY) + len(columns) + len(metrics)
        lines = []
        for number, raw in enumerate(body, 3):
            cells = raw.split("\t")
            if len(cells) != len(names):
                raise ValueError(f"primitives.tsv line {number}: {len(cells)} cells, the header has {len(names)}")
            kind, algorithm, provider, operation, key_size, phase, variant, status = (
                None if c == ABSENT else c for c in cells[:len(KEY)])
            lines.append(PrimitiveLine(kind, algorithm, provider, operation, None if key_size is None else int(key_size),
                                       phase, variant, status, dict(zip(columns, map(_number, cells[len(KEY):n_at]))),
                                       dict(zip(metrics, map(_count, cells[n_at:cv_at]))),
                                       dict(zip(metrics, map(_number, cells[cv_at:])))))
        return cls(columns, metrics, tuple(lines))
