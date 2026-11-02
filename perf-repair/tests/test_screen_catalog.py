import hashlib
import json
import logging
import shutil
from pathlib import Path

import pytest

from test_stages import run  # noqa: F401  the recorded run, grouped

from perfrepair.catalog.screening import SCREENING
from perfrepair.check.run import validate_run
from perfrepair.config.load import load
from perfrepair.grouping.__main__ import main as grouping_main
from perfrepair.inputs.resolve import InputError
from perfrepair.repair.__main__ import main as repair_main
from perfrepair.repair.dossier import dossier
from perfrepair.run_dir import GroupingPaths
from perfrepair.screen.catalog import CatalogMismatch, ai_review, load_catalog, screening_catalog
from perfrepair.validation.__main__ import main as validation_main

F = Path(__file__).parent / "fixtures" / "results" / "manifest.yaml"
DEMO = Path(__file__).parent / "fixtures" / "apps" / "demo"
PACKAGED_LINE = "screening.catalog: packaged catalog (no perfrepair.yaml); aiReview off"


def settings(tmp_path, text):
    path = tmp_path / "perfrepair.yaml"
    path.write_text(text)
    return path


def catalog_lines(caplog):
    return [r.getMessage() for r in caplog.records if r.name == "perfrepair.inputs"]


def test_no_perfrepair_yaml_is_the_packaged_catalog_logged_in_one_line(caplog):
    caplog.set_level(logging.INFO, "perfrepair")
    catalog = screening_catalog(None)
    assert catalog.path == SCREENING and catalog.identity() == {
        "source": "packaged", "sha256": hashlib.sha256(SCREENING.read_bytes()).hexdigest()}
    assert caplog.messages == [PACKAGED_LINE] and caplog.records[0].code == "default"
    assert screening_catalog(load(None, {}, {})).path == SCREENING and caplog.messages[-1] == PACKAGED_LINE


def test_a_file_without_the_key_says_so_and_names_ai_review(tmp_path, caplog):
    caplog.set_level(logging.INFO, "perfrepair")
    path = settings(tmp_path, "screening: {aiReview: true}\n")
    loaded = load(path, {}, {})
    assert screening_catalog(loaded).path == SCREENING and ai_review(loaded) is True
    assert catalog_lines(caplog) == [f"screening.catalog: packaged catalog (screening.catalog unset in {path.resolve()}); "
                               f"aiReview on"]


def test_a_configured_catalog_is_used_without_a_log_line(tmp_path, caplog):
    caplog.set_level(logging.INFO, "perfrepair")
    shutil.copy(SCREENING, tmp_path / "mine.yaml")
    catalog = screening_catalog(load(settings(tmp_path, "screening: {catalog: mine.yaml}\n"), {}, {}))
    assert catalog.source == str(tmp_path / "mine.yaml") and catalog.sha256 == screening_catalog(None).sha256
    assert catalog_lines(caplog) == [PACKAGED_LINE]


def test_a_configured_catalog_that_does_not_exist_is_missing_file_never_the_packaged_one(tmp_path):
    with pytest.raises(InputError, match=r"^missing_file: screening.catalog: .*nope.yaml \(file .* screening.catalog\)"):
        screening_catalog(load(settings(tmp_path, "screening: {catalog: nope.yaml}\n"), {}, {}))


@pytest.mark.parametrize("command", ["build", "dossier", "validation"])
def test_every_step_that_screens_exits_non_zero_on_a_missing_catalog(tmp_path, capsys, command):
    config = str(settings(tmp_path, "screening: {catalog: nope.yaml}\n"))
    run = tmp_path / "run"
    run.mkdir()
    if command == "build":
        code = grouping_main(["build", "--manifest", str(F), "--run", str(run), "--perfrepair-config", config])
    elif command == "dossier":
        code = repair_main(["dossier", "--run", str(run), "--app", "a", "--source", str(tmp_path),
                            "--perfrepair-config", config])
    else:
        with pytest.raises(SystemExit) as e:
            validation_main([str(run), "--perfrepair-config", config])
        code = e.value.code
    assert code != 0 and "missing_file: screening.catalog" in capsys.readouterr().err
    assert not (run / "grouping").exists()


def test_build_logs_the_packaged_catalog_without_perfrepair_yaml(tmp_path, capsys):
    assert grouping_main(["build", "--manifest", str(F), "--run", str(tmp_path)]) == 0
    assert capsys.readouterr().err.splitlines() == [PACKAGED_LINE]
    assert json.loads((tmp_path / "grouping" / "screen.json").read_text())["verdicts"]


def _other_catalog(tmp_path):
    other = tmp_path / "other.yaml"
    other.write_text(SCREENING.read_text() + "\n# a person's edit\n")
    return load_catalog(other)


def test_build_records_the_catalog_it_screened_by(run):  # noqa: F811
    doc = json.loads(GroupingPaths(run).screen.read_text())
    assert doc["schemaVersion"] == 5 and doc["catalog"] == load_catalog(SCREENING).identity()


def test_the_dossier_step_refuses_a_catalog_screen_json_was_not_screened_by(run, tmp_path):  # noqa: F811
    app = run / "apps" / "demo"
    app.mkdir(parents=True)
    for name in ("scopes.json", "app.json"):
        shutil.copy(DEMO / name, app / name)
    with pytest.raises(CatalogMismatch, match=r"^screening_catalog_mismatch: screen.json was screened by packaged"):
        dossier(run, "demo", F.parents[1] / "app", _other_catalog(tmp_path), echo=lambda _: None)
    assert not (app / "dossiers.json").exists()


def test_check_reports_the_mismatch_and_the_same_catalog_passes(run, tmp_path):  # noqa: F811
    assert validate_run(run, load_catalog(SCREENING))["grouping/screen.json"] == []
    [problem] = validate_run(run, _other_catalog(tmp_path))["grouping/screen.json"]
    assert problem.startswith("screening_catalog_mismatch: ")


def test_a_screen_json_with_a_malformed_catalog_identity_is_refused(run):  # noqa: F811
    path = GroupingPaths(run).screen
    doc = json.loads(path.read_text())
    path.write_text(json.dumps({**doc, "catalog": {"source": "packaged", "sha256": "x"}}))
    assert validate_run(run, load_catalog(SCREENING))["grouping/screen.json"] == [
        "catalog {'source': 'packaged', 'sha256': 'x'} is not {source, sha256}"]
