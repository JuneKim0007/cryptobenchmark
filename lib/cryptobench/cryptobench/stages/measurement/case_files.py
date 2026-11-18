"""Each case's pulled benchmarkData kept at process-N/cases/<case>.json; the process's benchmarkData.json merged from those files; order.txt, the
process's launch order."""
import json

from cryptobench.shared import paths
from cryptobench.shared.document.json_dump import json_text


def path(into, case):
    return paths.Measurement(into).case(case)


def opened(into):
    """The process's cases/; an earlier run's moved aside with its unit when this run published (layout.supersede)."""
    paths.Measurement(into).cases.mkdir(parents=True, exist_ok=True)


def ordered(into, cases):
    """The order this process launched its cases in, one id per line."""
    paths.Measurement(into).order.write_text("".join(f"{case}\n" for case in cases))


def merge(into, cases, data):
    """data from the kept files of cases, in their order: the first case's context, every case's benchmarks."""
    documents = [json.loads(path(into, case).read_text()) for case in cases]
    data.write_text(json_text({"context": documents[0].get("context") or {},
                               "benchmarks": [benchmark for document in documents for benchmark in document.get("benchmarks") or []]}))
