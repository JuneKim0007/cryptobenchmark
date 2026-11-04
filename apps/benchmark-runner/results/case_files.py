"""Each case's pulled benchmarkData kept at process-N/cases/<case>.json; the process's benchmarkData.json merged from those files."""
import json
import shutil

FOLDER = "cases"


def path(into, case):
    return into / FOLDER / f"{case}.json"


def cleared(into):
    """An earlier run's files would read as this process's cases."""
    shutil.rmtree(into / FOLDER, ignore_errors=True)
    (into / FOLDER).mkdir(parents=True)


def merge(into, cases, data):
    """data from the kept files of cases, in their order: the first case's context, every case's benchmarks."""
    documents = [json.loads(path(into, case).read_text()) for case in cases]
    data.write_text(json.dumps({"context": documents[0].get("context") or {},
                                "benchmarks": [benchmark for document in documents for benchmark in document.get("benchmarks") or []]}, indent=1))
