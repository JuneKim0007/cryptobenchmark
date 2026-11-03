import logging
import shutil
from contextlib import contextmanager
from pathlib import Path

from perfrepair.dto import PrimitiveRow, Summary
from perfrepair.dto.prompt import SystemPrompt, TaskPrompt
from perfrepair.ai.runtime.prompt import PromptLibrary
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.log.emit import EVENT_ATTR
from perfrepair.log.sink import to_event
from perfrepair.result.modes import mode_of

FIXTURE_DEVICE = Path(__file__).parent / "fixtures" / "results" / "test-api36-00000000"
LIBRARY = PromptLibrary.load()
GENERIC = mode_of(PerfMode())
LATENCY = mode_of(PerfMode(("latency",)))
LATENCY_ALLOC = mode_of(PerfMode(("latency", "memAlloc")))


def with_results(folder):
    """folder as a device folder: the recorded benchmark results copied in, since perf-repair writes beside them."""
    shutil.copytree(FIXTURE_DEVICE, folder, dirs_exist_ok=True)
    return folder


SYSTEM = SystemPrompt("test", "SYS")


def task(text, item="x"):
    return TaskPrompt("test", text, item)


def library_with(texts):
    """The packaged prompts with the named ones replaced by text."""
    unknown = sorted(set(texts) - set(LIBRARY.entries))
    assert not unknown, f"prompt_unknown: {unknown}"
    return PromptLibrary(LIBRARY.entries, {**LIBRARY.texts, **texts},
                         {**LIBRARY.sources, **{name: Path(f"<{name}>") for name in texts}})


def label_charter(schema):
    return library_with({"evaluate/worthiness": "SYS"}).charter("evaluate/worthiness", schema)


def row(rid, provider, algorithm="ALG-A", type_="TypeA", key_kind="secret", key_size=128, input_size=64,
        operation="OP1"):
    return PrimitiveRow(rid, type_, algorithm, provider, operation, key_size, input_size, "WARM", key_kind)


def summary(median, spread=1.0, n=50):
    """One process of n runs spread evenly over median ± spread, so the median is exact."""
    runs = tuple(median + spread * (2 * i / (n - 1) - 1) for i in range(n)) if n > 1 else (float(median),)
    return Summary(median, median - spread, median + spread, 0.01, n, median - spread / 4, median + spread / 4, (runs,))


QUIET = {"echo": lambda _: None}


CATALOG = {"source": "packaged", "sha256": "0" * 64}


@contextmanager
def captured_events():
    """Every event emitted inside the block, as the sink would write it, without a device folder."""
    events = []

    class Capture(logging.Handler):
        def emit(self, record):
            if getattr(record, EVENT_ATTR, None) is not None:
                events.append(to_event(record, "r1"))

    handler, logger = Capture(logging.DEBUG), logging.getLogger("perfrepair")
    level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield events
    finally:
        logger.removeHandler(handler)
        logger.setLevel(level)
