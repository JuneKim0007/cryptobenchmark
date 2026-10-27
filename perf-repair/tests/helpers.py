from pathlib import Path

from perfrepair.dto import PrimitiveRow, Summary
from perfrepair.dto.prompt import SystemPrompt, TaskPrompt
from perfrepair.ai.runtime.prompt import PromptLibrary

LIBRARY = PromptLibrary.load()
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
