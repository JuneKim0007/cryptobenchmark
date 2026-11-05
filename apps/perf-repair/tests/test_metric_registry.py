"""Every registry metric end to end: benchmark.json → rows → measurements.json → validator → evidence; none dropped."""
import json
from dataclasses import replace

import pytest

from perfrepair.data_handler.inbound.results import read_results
from perfrepair.dto.measurement import Measurements
from perfrepair.dto.metrics import BY_NAME, METRICS, NAMES
from perfrepair.dto.report import REPORTED
from perfrepair.dto.site import METRICS as DOSSIER_METRICS
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.result.evidence import build_evidence
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
    groups = {"groups": [{"id": "g", "family": "f", "description": "G", "members": [1, 2]}],
              "items": {"1": {"qualified": "TypeA|ALG-A|P1"}, "2": {"qualified": "TypeA|ALG-A|P2"}},
              "interop": {"status": "not_run", "pairs": []}}
    return rows, document, build_evidence(groups, rows, document.byRow, None, PerfMode(overall=True))


@pytest.mark.parametrize("metric", NAMES)
def test_a_registry_metric_reaches_every_stage(chain, metric):
    rows, document, evidence = chain
    assert {r.rowId for r in rows} == {"from", "to"}
    assert document.byRow["to"][metric].median == pytest.approx(21.5)
    assert document.byRow["to"][metric].kind == (BY_NAME[metric].kinds[0] if BY_NAME[metric].kinds else None)
    assert validate_measurements(document, rows) == []
    member = next(m for c in evidence[0].configurations for m in c.members if m.rowId == "to")
    assert member.metrics[metric].median == pytest.approx(21.5)
    pair = next(p for c in evidence[0].configurations for p in c.pairs if p.toItem == "TypeA|ALG-A|P2")
    compared = {c.metric: c for c in pair.metrics}[metric]
    assert compared.ratio == pytest.approx(21.5 / 41.5) and compared.pImprove == 1.0


def test_a_metric_outside_the_registry_is_refused(chain):
    rows, document, _ = chain
    document.byRow["to"]["allocations"] = document.byRow["to"]["allocationCount"]
    assert validate_measurements(document, rows) == ["to.allocations: not a registry metric"]


def test_a_kind_outside_the_registry_is_refused(chain):
    rows, document, _ = chain
    kinded = next(m for m in METRICS if m.kinds)
    document.byRow["to"][kinded.name] = replace(document.byRow["to"][kinded.name], kind="guessed")
    assert validate_measurements(document, rows) == [f"to.{kinded.name}: kind 'guessed' is not {' or '.join(kinded.kinds)}"]


def test_every_kept_metric_list_is_the_registry():
    assert DOSSIER_METRICS == NAMES and tuple(name for name, _ in REPORTED) == NAMES
    assert len({key for m in METRICS for key in m.selects}) == sum(len(m.selects) for m in METRICS)
