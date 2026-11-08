"""apps-index.tsv: one line per app folder from its files and its latest guide run; scripted model, no device."""
import csv
import shutil

from test_guide import APP, FAKE_ROOT
from test_guide_targets import base  # noqa: F401  the recorded run and two-app loop
from test_stages import run  # noqa: F401

from perfrepair import failure
from perfrepair.ai.select.command import dry_run
from perfrepair.app.facts.path_id import path_id
from perfrepair.guide import app_steps as guide_steps
from perfrepair.guide.index import main as index_main
from perfrepair.log import attach
from perfrepair.run_dir import APPS_INDEX, EDITS


def _rows(device):
    with open(device / APPS_INDEX, newline="") as f:
        return {r["app"]: r for r in csv.DictReader(f, delimiter="\t")}


def _go(base, roots, **kw):  # noqa: F811
    """As the guide command runs: its events reach the device folder's events.jsonl."""
    def body():
        attach(base.run_dir)
        return base.go(roots, **kw)[0]
    attach()
    return failure.reported(body)


def _android(base, parent, settings=None):  # noqa: F811
    path = base.tmp / "apps" / parent / "android"
    shutil.copytree(APP, path)
    if settings:
        (path / "settings.gradle").write_text(settings)
    return path.resolve()


def test_two_trees_of_one_folder_name_differ_and_a_stop_is_their_code(base):  # noqa: F811
    a, b = _android(base, "x"), _android(base, "y", "rootProject.name = 'Named'\n")
    code = _go(base, [a, b], conversations=dry_run())
    rows = _rows(base.run_dir)
    assert code == 1 and (rows[path_id(a)]["project"], rows[path_id(b)]["project"]) == ("x/android", "Named")
    ra = rows[path_id(a)]
    assert (ra["source"], ra["stage"], ra["stop"], ra["checked"], ra["replace"]) == (str(a), "replace", "no_replacement",
                                                                                      "no", "0")
    assert int(ra["sites"]) >= int(ra["scopes"]) > 0 and int(ra["drop-in"]) + int(ra["local-edit"]) > 0
    assert int(ra["fixed"]) + int(ra["notFixed"]) == int(ra["scopes"]) and int(ra["unknown_default"]) <= int(ra["notFixed"])


def test_a_later_run_that_stops_nowhere_clears_the_stop_and_the_command_rewrites_it(base, monkeypatch):  # noqa: F811
    a = _android(base, "x")
    with monkeypatch.context() as m:
        m.setattr(guide_steps, "repair_main", lambda argv: 1)
        assert _go(base, [a]) == 1 and _rows(base.run_dir)[path_id(a)]["stop"] == "edit_invalid"
    code = _go(base, [a], reuse=False)
    row = _rows(base.run_dir)[path_id(a)]
    assert code == 0 and (row["stop"], row["reason"], row["stage"]) == ("", "", "harness") and int(row["replace"]) > 0
    # a stop before the edit leaves the earlier edits.json and harness.yaml; older than replacements.json, they do not count
    with monkeypatch.context() as m:
        m.setattr(guide_steps, "repair_main", lambda argv: 1)
        assert _go(base, [a], reuse=False) == 1 and _rows(base.run_dir)[path_id(a)]["stage"] == "replace"
    assert (base.run_dir / path_id(a) / EDITS).is_file()
    (base.run_dir / APPS_INDEX).unlink()
    assert index_main(["--device-results", str(base.run_dir)]) == 0 and path_id(a) in _rows(base.run_dir)


def test_a_device_app_reaches_its_report_and_is_checked(base, monkeypatch):  # noqa: F811
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(FAKE_ROOT))
    a = _android(base, "x")
    assert _go(base, [a], device=True) == 0
    row = _rows(base.run_dir)[path_id(a)]
    assert (row["stage"], row["checked"]) == ("report", "yes")


def test_columns_of_a_step_past_the_reached_stage_stay_empty(base, monkeypatch):  # noqa: F811
    a = _android(base, "x")
    assert _go(base, [a]) == 0 and int(_rows(base.run_dir)[path_id(a)]["replace"]) > 0
    source = sorted((a / "src").rglob("*.java"))[0]
    source.write_text(source.read_text() + "\n")
    # the rerun stops before its dossier: the earlier dossiers.json and replacements.json stay, older than scopes.json
    monkeypatch.setattr(guide_steps, "dossier", lambda *_, **__: (_ for _ in ()).throw(ValueError("no_dossier: x")))
    assert _go(base, [a]) == 1
    row = _rows(base.run_dir)[path_id(a)]
    assert (row["stage"], row["replace"], row["notOffered"], row["checked"]) == ("app", "0", "0", "no")
