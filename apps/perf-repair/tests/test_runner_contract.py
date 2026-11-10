"""The fake pipelines perf-repair's tests run print the real runner's prefixes, so a fake cannot pass a line the runner never prints."""
import ast
from pathlib import Path

from perfrepair.data_handler.outbound.benchmark_runner import IDENTITY, WROTE_MANIFEST
from perfrepair.device.delta_estimate import TOOK

REPO = Path(__file__).parents[3]
FAKES = sorted((Path(__file__).parent / "fixtures").glob("*/apps/benchmark-runner/pipeline.py"))
PRODUCERS = {"wrote:     ": REPO / "apps/benchmark-runner/results/manifest.py", "identity:  ": REPO / "apps/benchmark-runner/pipeline.py",
             "took:      ": REPO / "apps/benchmark-runner/stages/took.py"}


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


def test_the_patterns_are_the_ones_the_runner_tests_pin():
    assert WROTE_MANIFEST.pattern == r"^wrote:\s+(.*/manifest\.yaml)$"
    assert IDENTITY.pattern == r"^identity:\s+(\{.*\})$"
    assert TOOK.pattern == r"^took:\s+prepare and measure in (?P<s>[0-9.]+)s$"


def test_the_real_runner_prints_each_prefix():
    for prefix, producer in PRODUCERS.items():
        assert any(text.startswith(prefix) for text in printed_prefixes(producer)), (prefix, producer)


def test_every_fake_pipeline_uses_the_runners_exact_prefixes():
    assert len(FAKES) == 2
    for fake in FAKES:
        for text in printed_prefixes(fake):
            for prefix in PRODUCERS:
                label = prefix.rstrip()
                if text.startswith(label):
                    assert text.startswith(prefix), (fake, text)
