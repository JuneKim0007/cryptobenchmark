"""Run: one probe_device call's settings; the probe and the planned stages run in order, each with its event."""
from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from .. import run_dir as rd
from ..data_handler.outbound.benchmark_runner import run_pipeline
from ..dto.bundled import BundledPolicy
from ..dto.event import END
from ..grouping.build.stage import build_stage
from ..log import emit, step
from ..screen.catalog import Catalog
from ..stop.halt import Coded
from .energy import report_invalid
from .inbound import write_inbound
from .primitives import write_primitives
from .primitives_missing import MissingList


@dataclass(frozen=True)
class Run:
    """What one probe_device call runs with; probed: the probe is current before the benchmark, so a host run reuses it."""
    root: Path
    folder: Path
    catalog: Catalog
    config: Path | None
    on_device: bool
    echo: Callable[[str], None]
    benchmark: Path | str | None
    probed: bool = False
    bundled: BundledPolicy = BundledPolicy()
    missing: MissingList = field(default_factory=MissingList)


def _same_folder(manifest: Path, folder: Path) -> None:
    if manifest.parent.resolve() != folder.resolve():
        raise Coded(f"device_id_changed: --identify named {folder.name}, the probe wrote {manifest.parent.name}")


def _measure(r: Run, steps: dict) -> None:
    # on a host, a kept probe is reused by the benchmark run itself, so the capture is the one the plan judged
    fresh = steps["probe"] and not r.probed
    reuse = () if r.on_device or fresh else ("--discovery", "reuse")
    manifest = run_pipeline(r.config, r.root, "device" if r.on_device else "bench", benchmark=r.benchmark, echo=r.echo,
                            extra=reuse, device=r.folder)
    _same_folder(manifest, r.folder)
    report_invalid(manifest)


@contextmanager
def _ran(stage: str, reason: str):
    with step("device", stage, detail=reason) as s:
        s.outcome, s.detail = "ran", reason
        yield


def _screen(r: Run, steps: dict) -> None:
    if steps["screen"]:
        with _ran("screen", steps["screen"]):
            build_stage(r.folder / rd.MANIFEST, r.folder, r.catalog, echo=r.echo)


def run_stages(r: Run, steps: dict) -> None:
    if steps["benchmark"]:
        with _ran("benchmark", steps["benchmark"]):
            _measure(r, steps)
        if steps["probe"] and not r.probed:
            emit("device", "probe", END, outcome="ran", detail=steps["probe"], data={"ranWith": "benchmark"})
    if steps["inbound"]:
        with _ran("inbound", steps["inbound"]):
            for line in write_inbound(r.folder):
                r.echo(line)
    _screen(r, steps)
    if steps["primitives"]:
        with _ran("primitives", steps["primitives"]):
            r.echo(write_primitives(r.folder))


def run_probe(r: Run, steps: dict) -> None:
    if steps["probe"]:
        with _ran("probe", steps["probe"]):
            _same_folder(run_pipeline(r.config, r.root, "device" if r.on_device else "configure", benchmark=r.benchmark,
                                      echo=r.echo, extra=("--probe",), device=r.folder), r.folder)
    _screen(r, steps)
