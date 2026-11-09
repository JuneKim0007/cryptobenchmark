"""After a delta merged or a whole rerun: inbound and primitives made again, device.yaml rewritten to vouch for them."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from cryptobench.paths import RunTree
from .. import run_dir as rd
from ..dto.used import names_digest
from ..files import sha256_file
from .inbound import write_inbound
from .primitives import inputs as primitive_inputs
from .primitives import write_primitives


def rebuilt(folder: Path, added: frozenset[str], echo: Callable[[str], None]) -> None:
    """added: the used items the benchmark now holds, joined to device.yaml's measured set."""
    folder = Path(folder)
    record, _ = rd.load_device_record(folder)
    rd.drop_device_record(folder)
    for line in write_inbound(folder):
        echo(line)
    echo(write_primitives(folder))
    if record is None:
        return
    benchmark = dict(record.benchmark)
    if benchmark:
        items = sorted(set(benchmark.get("items") or ()) | added)
        benchmark.update(items=items, used=names_digest(items))
    rd.write_device_record(folder, replace(record, manifest=sha256_file(RunTree(folder).manifest),
                                           primitives=primitive_inputs(folder), benchmark=benchmark))
