"""The fake pipelines perf-repair's tests run print the runner's own labels (cryptobench.shared.log.stdout), so a fake cannot pass a line the runner never prints."""
import ast
from pathlib import Path

from cryptobench.shared.log.stdout import IDENTITY, TOOK, WROTE

FAKES = sorted((Path(__file__).parent / "fixtures").glob("*/apps/benchmark-runner/pipeline.py"))
PREFIXES = (WROTE, IDENTITY, TOOK)


def printed_prefixes(path: Path) -> set[str]:
    """The start of every string literal or f-string a print call begins with."""
    found = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "print" and node.args:
            first = node.args[0]
            first = first.left if isinstance(first, ast.BinOp) else first
            part = first.values[0] if isinstance(first, ast.JoinedStr) and first.values else first
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                found.add(part.value)
    return found


def test_every_fake_pipeline_uses_the_runners_exact_prefixes():
    assert len(FAKES) == 2
    for fake in FAKES:
        for text in printed_prefixes(fake):
            for prefix in PREFIXES:
                label = prefix.rstrip()
                if text.startswith(label):
                    assert text.startswith(prefix), (fake, text)
