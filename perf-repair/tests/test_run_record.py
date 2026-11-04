"""RunRecord: run.id, run.onExisting, the done marks it owns, and that no other module writes them."""
import re
from pathlib import Path

import pytest

from perfrepair.dto.coded import InputError
from perfrepair.files import read_json
from perfrepair.run_dir import DEVICE, RUNS, AppPaths
from perfrepair.run_dir.run_record import (
    DONE,
    FAILED,
    RESUME,
    RUNNING,
    SKIP,
    STOPPED,
    RunRecord,
)

SRC = Path(__file__).parents[1] / "src" / "perfrepair"
INPUTS = {"tree": "t", "measured": False}


def device(tmp_path, apps=("a",)):
    folder = tmp_path / "dev"
    for app in apps:
        (folder / app).mkdir(parents=True)
        (folder / app / "app.json").write_text("{}")
    (folder / DEVICE).write_text("schemaVersion: 1\n")
    return folder


def done(folder, run_id=None, **kw):
    r = RunRecord.open(folder, run_id, **kw)
    r.app_step("a", "app")
    r.app_done("a", INPUTS, "ok")
    r.close()
    return r


def test_an_empty_id_is_a_new_timestamp_never_an_existing_run(tmp_path):
    folder = device(tmp_path)
    first, second = done(folder), done(folder)
    assert re.fullmatch(r"\d{8}T\d{6}Z(-\d+)?", first.id) and first.id != second.id
    # a generated id never overwrites: the first run's done mark stays
    assert RunRecord.open(folder).is_done("a", INPUTS)


def test_overwrite_clears_every_done_mark_and_the_device_record(tmp_path):
    folder = device(tmp_path)
    done(folder, "r1")
    r = RunRecord.open(folder, "r1")
    assert not r.is_done("a", INPUTS) and not (folder / DEVICE).exists()
    assert read_json(folder / RUNS / "run_r1.json")["apps"] == {}


def test_resume_keeps_them_and_skip_runs_nothing(tmp_path):
    folder = device(tmp_path)
    done(folder, "r1")
    r = RunRecord.open(folder, "r1", on_existing=RESUME)
    assert r.is_done("a", INPUTS) and (folder / DEVICE).exists() and r.doc["apps"]["a"]["status"] == DONE
    r.close()
    with pytest.raises(InputError, match=r"^run_exists: run r1 has a record"):
        RunRecord.open(folder, "r1", on_existing=SKIP)


def test_each_step_and_outcome_is_on_disk_at_once(tmp_path):
    folder = device(tmp_path)
    r = RunRecord.open(folder, "r1")
    on_disk = lambda: read_json(r.path)
    assert on_disk()["device"] == {"status": RUNNING}
    r.device_done()
    r.app_step("a", "dossier")
    assert on_disk()["device"] == {"status": DONE} and on_disk()["apps"]["a"] == {"status": RUNNING, "step": "dossier"}
    r.app_failed("a", "replace", "replace_failed: x")
    assert on_disk()["apps"]["a"] == {"status": FAILED, "step": "replace", "reason": "replace_failed: x"}
    r.device_done(STOPPED, "grouping", "interrupted")
    assert on_disk()["device"] == {"status": STOPPED, "step": "grouping", "reason": "interrupted"}


def test_the_first_step_of_a_rerun_clears_the_done_mark_and_the_report(tmp_path):
    folder = device(tmp_path)
    done(folder)
    paths = AppPaths(folder, "a")
    paths.report.write_text("{}")
    r = RunRecord.open(folder)
    r.app_step("a", "app")
    assert not paths.finished.exists() and not paths.report.exists()
    paths.report.write_text("{}")
    r.app_step("a", "dossier")
    assert paths.report.exists()


@pytest.mark.parametrize("content", ["", '{"tree": ', "[]", "null", '{"tree": "t", "measured": false}'])
def test_an_unreadable_or_old_done_mark_is_not_done(tmp_path, content):
    folder = device(tmp_path)
    AppPaths(folder, "a").finished.write_text(content)
    assert not RunRecord.open(folder).is_done("a", INPUTS)


def test_reused_says_the_outcome_it_was_done_with(tmp_path):
    folder = device(tmp_path)
    r = RunRecord.open(folder)
    r.app_done("a", INPUTS, "no_options")
    assert r.app_reused("a") == "no_options" and r.doc["apps"]["a"]["reused"]


def _writers(pattern: str) -> list[str]:
    """Modules whose code names the pattern."""
    return sorted(str(p.relative_to(SRC)) for p in SRC.rglob("*.py") if re.search(pattern, p.read_text()))


def test_only_the_record_writes_the_run_record_and_the_done_marks():
    assert _writers(r"\bFINISHED\b") == ["run_dir/__init__.py", "run_dir/layout.py"]
    assert _writers(r"\bRUNS\b") == ["run_dir/__init__.py", "run_dir/layout.py", "run_dir/run_record.py"]
    assert _writers(r"\.finished\b") == ["run_dir/run_record.py"]
    assert _writers(r'"run_\{') == ["run_dir/run_record.py"]
    assert _writers(r"\bwrite_device_record\b") == ["device/stage.py", "run_dir/__init__.py", "run_dir/run_record.py"]
    assert _writers(r"DEVICE\)\.unlink|DEVICE, yaml") == ["run_dir/run_record.py"]
