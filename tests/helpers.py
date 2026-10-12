"""Builders shared by the tests: fake rows and summaries."""
from perfrepair.dto import PrimitiveRow, Summary


def row(rid, provider, algorithm="ALG-A", type_="TypeA", key_kind="secret", key_size=128, input_size=64,
        operation="OP1"):
    return PrimitiveRow(rid, type_, algorithm, provider, operation, key_size, input_size, "WARM", key_kind)


def summary(median, spread=1.0):
    return Summary(median, median - spread, median + spread, 0.01, 50)
