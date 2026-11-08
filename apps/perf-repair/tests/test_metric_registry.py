"""Every registry metric end to end: benchmark.json → rows → measurements.json → validator; none dropped."""
import json
from dataclasses import replace

import pytest

from perfrepair.data_handler.inbound.results import read_results
from perfrepair.dto.measurement import Measurements
from perfrepair.dto.metrics import BY_NAME, METRICS, NAMES
from perfrepair.validation.measurements import validate_measurements

RUNS = {"from": [40.0, 41.0, 42.0, 43.0], "to": [20.0, 21.0, 22.0, 23.0]}


def _case(cid: str, provider: str, runs: list[float]) -> dict:
    metrics = {m.name: {"iterations": 1, "runs": runs} | ({"kind": m.kinds[0]} if m.kinds else {}) for m in METRICS}
    return {"id": cid, "type": "TypeA", "algorithm": "ALG-A", "provider": provider, "operation": "OP1",
            "keySize": 128, "inputSize": 64, "parameters": {}, "metrics": metrics}


@pytest.fixture
def chain(tmp_path):
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps({"cases": [_case("from", "P1", RUNS["from"]), _case("to", "P2", RUNS["to"])]}))
    rows, by_row, _ = read_results(path)
    document = Measurements.from_json(json.loads(json.dumps(Measurements({}, [], by_row).to_json())))
    return rows, document


@pytest.mark.parametrize("metric", NAMES)
def test_a_registry_metric_reaches_every_stage(chain, metric):
    rows, document = chain
    assert {r.rowId for r in rows} == {"from", "to"}
    assert document.byRow["to"][metric].median == pytest.approx(21.5)
    assert document.byRow["to"][metric].kind == (BY_NAME[metric].kinds[0] if BY_NAME[metric].kinds else None)
    assert validate_measurements(document, rows) == []


def test_a_metric_outside_the_registry_is_refused(chain):
    rows, document = chain
    document.byRow["to"]["allocations"] = document.byRow["to"]["allocationCount"]
    assert validate_measurements(document, rows)


def test_a_kind_outside_the_registry_is_refused(chain):
    rows, document = chain
    kinded = next(m for m in METRICS if m.kinds)
    document.byRow["to"][kinded.name] = replace(document.byRow["to"][kinded.name], kind="guessed")
    assert validate_measurements(document, rows)


def test_every_kept_metric_list_is_the_registry():
    assert len({key for m in METRICS for key in m.selects}) == sum(len(m.selects) for m in METRICS)
