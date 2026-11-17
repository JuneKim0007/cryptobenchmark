"""run.resumeBlockRuns: a pass's runs in blocks of k consecutive runs; a block's record, written once its last run closed, lets a rerun of the
same identity keep it (stages/measurement/resume.py)."""
import dataclasses, pathlib

from cryptobench.shared import paths
from cryptobench.shared.digest.tree import file_digest
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.shared.document.write import write_text
from cryptobench.pipeline.warn import warn

SCHEMA = 1
FINISHED, BOOT_CHANGED = "finished", "boot_changed"


@dataclasses.dataclass(frozen=True)
class Blocks:
    """One pass's runs: folder is the pass's folder, label its name (None for the single pass); boot() reads the device's boot id, None on a host."""
    folder: pathlib.Path
    size: int
    repetitions: int
    identity: dict
    label: str | None = None
    boot: object = lambda: None


def ranges(repetitions, size):
    """(block, first run, last run), blocks numbered from 1; the last block may be shorter."""
    return [(block, first, min(first + size - 1, repetitions)) for block, first in enumerate(range(1, repetitions + 1, size), 1)]


def where(folder, label, block):
    return f"{label + ' pass ' if label else ''}block {block} ({paths.Measurement(folder).block(block)})"


def recorded(folder):
    """{block: record} of the pass folder's records; after a publish only the blocks the rerun keeps are left."""
    return {record["block"]: record for record in map(read_yaml, paths.Measurement(folder).block_records())}


def run_files(run, pass_folder):
    """{path under the run's folder: sha256} of every file it holds; a pass folder that is its only run's leaves its blocks/ out."""
    blocks = paths.Measurement(pass_folder).blocks
    return {path.relative_to(run).as_posix(): file_digest(path) for path in sorted(run.rglob("*")) if path.is_file() and not path.is_relative_to(blocks)}


def measured(blocks, folder, measure, keep, problems):
    """A recorded block's runs go through keep(repetition), their recorded problem lines joining problems; any other block is measured run by run,
    each run's lines being what measure(repetition) added to problems, then recorded."""
    kept = recorded(blocks.folder)
    for block, first, last in ranges(blocks.repetitions, blocks.size):
        if block in kept:
            for run in kept[block]["processes"]:
                keep(run["repetition"])
                problems += run["problems"]
            continue
        start, runs = blocks.boot(), []
        for repetition in range(first, last + 1):
            before = len(problems)
            measure(repetition)
            runs.append(run_entry(blocks, folder, repetition, problems[before:]))
        write(blocks, block, (first, last), runs, (start, blocks.boot()), problems)


def run_entry(blocks, folder, repetition, lines):
    into = folder(repetition)
    return {"repetition": repetition, "folder": into.relative_to(blocks.folder).as_posix(), "problems": list(lines),
            "files": run_files(into, blocks.folder)}


def write(blocks, block, span, runs, boot, problems):
    """Durable and exclusive: a stop before it leaves the block unfinished, and no record is ever replaced."""
    outcome = FINISHED if boot[0] == boot[1] else BOOT_CHANGED
    if outcome == BOOT_CHANGED:
        warn(f"boot_changed: {where(blocks.folder, blocks.label, block)}: the device restarted during runs {span[0]}-{span[1]}; a rerun measures them again",
             problems)
    record = {"schemaVersion": SCHEMA, "pass": blocks.label, "block": block, "runs": {"first": span[0], "last": span[1]},
              "repetitions": blocks.repetitions, "size": blocks.size, "identity": blocks.identity, "bootId": {"start": boot[0], "end": boot[1]},
              "outcome": outcome, "processes": runs}
    path = paths.Measurement(blocks.folder).block(block)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path, dump_yaml(record), durable=True, exclusive=True)
