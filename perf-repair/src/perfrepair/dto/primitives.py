"""primitives.tsv: one line per measured primitive, a median column per (metric, input size), n, and cv per metric."""
from __future__ import annotations

from dataclasses import dataclass

SCHEMA_VERSION = 1
SCHEMA_LINE = f"#schemaVersion\t{SCHEMA_VERSION}"
KEY = ("type", "algorithm", "provider", "operation", "keySize", "phase", "status")
ABSENT = "-"
SIGNIFICANT = 4


def rounded(x: float | None) -> float | None:
    """The table is a view for reading; statistics stay in measurements.json, so 4 significant digits suffice."""
    return None if x is None else float(f"{x:.{SIGNIFICANT}g}")


def column(metric: str, input_size: int | None) -> str:
    return f"{metric}@{ABSENT if input_size is None else input_size}"


def cv_column(metric: str) -> str:
    return f"{metric}.cv"


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


@dataclass(frozen=True)
class PrimitiveLine:
    type: str
    algorithm: str
    provider: str
    operation: str
    keySize: int | None
    phase: str | None
    status: str
    medians: dict[str, float | None]
    n: int
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
        return (*KEY, *self.columns, "n", *(cv_column(m) for m in self.metrics))

    def to_tsv(self) -> str:
        out = [SCHEMA_LINE, "\t".join(self.header)]
        for line in self.lines:
            cells = [*line.key, *(line.medians.get(c) for c in self.columns), line.n, *(line.cv.get(m) for m in self.metrics)]
            out.append("\t".join(_text(c) for c in cells))
        return "\n".join(out) + "\n"

    @classmethod
    def from_tsv(cls, text: str) -> "PrimitivesTable":
        first, header, *body = text.rstrip("\n").split("\n")
        if first != SCHEMA_LINE:
            raise ValueError(f"primitives.tsv first line {first!r} is not {SCHEMA_LINE!r}")
        names = header.split("\t")
        n_at = names.index("n")
        if tuple(names[:len(KEY)]) != KEY:
            raise ValueError(f"primitives.tsv header starts {names[:len(KEY)]}, not {list(KEY)}")
        columns, metrics = tuple(names[len(KEY):n_at]), tuple(c.removesuffix(".cv") for c in names[n_at + 1:])
        lines = []
        for number, raw in enumerate(body, 3):
            cells = raw.split("\t")
            if len(cells) != len(names):
                raise ValueError(f"primitives.tsv line {number}: {len(cells)} cells, the header has {len(names)}")
            kind, algorithm, provider, operation, key_size, phase, status = (None if c == ABSENT else c for c in cells[:len(KEY)])
            lines.append(PrimitiveLine(kind, algorithm, provider, operation, None if key_size is None else int(key_size),
                                       phase, status, dict(zip(columns, map(_number, cells[len(KEY):n_at]))),
                                       int(cells[n_at]), dict(zip(metrics, map(_number, cells[n_at + 1:])))))
        return cls(columns, metrics, tuple(lines))
