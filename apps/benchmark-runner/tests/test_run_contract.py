"""Every effective run key :config writes and every pipeline.py flag is classified DATA or NOT_DATA (shared/results/run_record.py); a DATA value
that is unresolved refuses the run record."""
import re, types

import pytest
import yaml

import pipeline
from cryptobench.shared import paths
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.results import run_record

RUN_DOCUMENT = paths.repo().gradle_root / "modules/config/src/main/kotlin/global/RunDocument.kt"


def kotlin_run_keys():
    """The keys RunDocument.parse expects of run, by their constants' values."""
    text = RUN_DOCUMENT.read_text()
    constants = dict(re.findall(r'private const val (\w+) = "(\w+)"', text))
    names = re.search(r"expectKeys\(document, listOf\(([^)]*)\), path\)", text).group(1)
    return {constants[name.strip()] for name in names.split(",")}


def test_every_run_key_config_writes_is_classified():
    assert kotlin_run_keys() == set(run_record.RUN_KEYS)


def test_every_pipeline_flag_is_classified():
    flags = {action.dest for action in pipeline.parser()._actions if action.dest != "help"}
    assert flags == set(run_record.FLAGS)


def test_every_data_flag_names_its_record_field_and_every_not_data_row_says_why():
    for table in (run_record.RUN_KEYS, run_record.FLAGS):
        assert all(kind in (run_record.DATA, run_record.NOT_DATA) for kind, _ in table.values())
    assert all(why for kind, why in run_record.FLAGS.values())
    assert all(why for kind, why in run_record.RUN_KEYS.values() if kind == run_record.NOT_DATA)


OPTIONS = types.SimpleNamespace(suppress_errors="", energy_accept_unresponsive=False)
RUN = {key: 1 for key, (kind, absent) in run_record.RUN_KEYS.items() if absent is None}


@pytest.mark.parametrize("key", [key for key, (kind, absent) in run_record.RUN_KEYS.items() if kind == run_record.DATA and absent is None])
def test_an_unresolved_data_run_key_refuses_the_record(key):
    with pytest.raises(CommandError, match=f"^missing_field: run.{key} in effective.yaml$"):
        run_record.resolved({"run": {k: v for k, v in RUN.items() if k != key}}, OPTIONS)


def test_an_unresolved_data_flag_and_an_unclassified_run_key_refuse_the_record():
    with pytest.raises(CommandError, match="^missing_field: --energy-accept-unresponsive"):
        run_record.resolved({"run": RUN}, types.SimpleNamespace(suppress_errors=""))
    with pytest.raises(CommandError, match="^unclassified: run.isolation"):
        run_record.resolved({"run": {**RUN, "isolation": "case"}}, OPTIONS)
    run_record.resolved({"run": RUN}, OPTIONS)


def test_the_record_holds_every_data_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(run_record.identity, "device", lambda _capture: {})
    monkeypatch.setattr(run_record.identity, "code", lambda: {})
    effective = tmp_path / "effective.yaml"
    effective.write_text(yaml.safe_dump({"run": RUN}))
    record = run_record.of(effective, tmp_path / "probe.yaml", {}, types.SimpleNamespace(suppress_errors="UNLOCKED", energy_accept_unresponsive=True))
    assert {field: record[field] for kind, field in run_record.FLAGS.values() if kind == run_record.DATA} == {
        "suppressErrors": ["UNLOCKED"], "energyAcceptUnresponsive": True}
