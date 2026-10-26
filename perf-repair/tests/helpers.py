from perfrepair.dto import PrimitiveRow, Summary
from perfrepair.dto.prompt import SystemPrompt, TaskPrompt
from perfrepair.ai.runtime.prompt import PromptLibrary

LIBRARY = PromptLibrary.load()
SYSTEM = SystemPrompt("test", "SYS")


def task(text, item="x"):
    return TaskPrompt("test", text, item)


def label_charter(schema):
    return PromptLibrary.from_texts({"evaluate/worthiness": "SYS"}).charter("evaluate/worthiness", schema)


def row(rid, provider, algorithm="ALG-A", type_="TypeA", key_kind="secret", key_size=128, input_size=64,
        operation="OP1"):
    return PrimitiveRow(rid, type_, algorithm, provider, operation, key_size, input_size, "WARM", key_kind)


def summary(median, spread=1.0):
    return Summary(median, median - spread, median + spread, 0.01, 50, median - spread / 4, median + spread / 4)


QUIET = {"echo": lambda _: None}
