"""#78's flows across runs on the fake pipeline and the dry-run gateway: what reruns, how many device runs and model calls."""
import logging
import shutil
from pathlib import Path

import pytest
import yaml

from perfrepair import run_dir as rd
from perfrepair.ai.runtime.engine.outbox import active_fingerprint
from perfrepair.check.run import validate_run
from perfrepair.files import read_json
from perfrepair.guide.command import main as guide
from perfrepair.run_dir import GroupingPaths
from perfrepair.screen.catalog import screening_catalog

F = Path(__file__).parent / "fixtures"
APP = F / "app"
FOLDER = "fake-api36-00000000"
BUNDLED_FIRST = "bundled: [{artifact: 'g:a:1', create: Aaa}]"
OLD_ITEMS = 4


class Flow:
    def __init__(self, tmp_path, capsys):
        self.tmp, self.capsys = tmp_path, capsys
        self.root, self.global_yaml = tmp_path / "results", tmp_path / "global.yaml"
        self.device = self.root / FOLDER
        self.paths = GroupingPaths(self.device)
        self.global_yaml.write_text("schemaVersion: 1\nselection: {testSet: x.yaml}\nproviders: {bundled: []}\n")
        self.grouping = {"noRerun": True}

    def settings(self, text=None):
        path = self.tmp / "perfrepair.yaml"
        document = {"paths": {"results": str(self.root)}, "device": {"benchmark": {"config": str(self.global_yaml)},
                                                                     "grouping": self.grouping}}
        path.write_text(text if text is not None else yaml.safe_dump(document))
        return path

    def run(self, text=None):
        guide(["--app", str(APP), "--agent", "dry-run", "--perfrepair-config", str(self.settings(text))])
        return [line for line in self.capsys.readouterr().out.splitlines() if line.startswith(("device ", "guide "))]

    def calls(self):
        journal = self.paths.journal
        return len(journal.read_text().splitlines()) if journal.is_file() else 0

    def device_runs(self):
        log = self.root / "runs.log"
        return len(log.read_text().splitlines()) if log.is_file() else 0

    def add_provider(self):
        self.global_yaml.write_text(self.global_yaml.read_text().replace("bundled: []", BUNDLED_FIRST))

    def remove_provider(self):
        self.global_yaml.write_text(self.global_yaml.read_text().replace(BUNDLED_FIRST, "bundled: []"))

    def problems(self):
        out = validate_run(self.device, screening_catalog(None))
        return {k: v for k, v in out.items() if v}


@pytest.fixture
def flow(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    return Flow(tmp_path, capsys)


def _group_by_name(paths):
    doc = read_json(paths.groups)
    return {e["qualified"]: e["group"] for e in doc["items"].values()}


def test_a_first_run_asks_every_item_once(flow):
    lines = flow.run()
    assert f"guide grouping: ok: ran: {OLD_ITEMS} of {OLD_ITEMS} items asked" in lines
    assert flow.calls() == OLD_ITEMS and flow.device_runs() == 1 and flow.problems() == {}


def test_nothing_changed_is_no_call_no_device_run_and_grouping_reused(flow):
    flow.run()
    before = flow.paths.groups.stat().st_mtime_ns
    lines = flow.run()
    assert "guide grouping: ok: reused" in lines and flow.calls() == OLD_ITEMS and flow.device_runs() == 1
    assert flow.paths.groups.stat().st_mtime_ns == before


def test_a_provider_added_asks_only_its_new_items_and_rebuilds_the_groups(flow):
    flow.run()
    kept = _group_by_name(flow.paths)
    outbox = active_fingerprint(flow.paths.root)
    ids_before = {e["qualified"]: n for n, e in read_json(flow.paths.groups)["items"].items()}
    flow.add_provider()
    lines = flow.run()
    groups = _group_by_name(flow.paths)
    assert flow.device_runs() == 2 and active_fingerprint(flow.paths.root) == outbox
    # AES/GCM and SHA-256 of the new provider; its MD5 is screened out and grouped by code
    assert flow.calls() == OLD_ITEMS + 2 and f"guide grouping: ok: ran: 2 of {OLD_ITEMS + 2} items asked" in lines
    assert {q: g for q, g in groups.items() if q in kept} == kept
    new = [q for q in groups if q.endswith("|Aaa")]
    assert len(new) == 3 and all(groups[q] for q in new)
    assert any(ids_before[q] != n for n, q in ((n, e["qualified"]) for n, e in read_json(flow.paths.groups)["items"].items())
               if q in ids_before), "the new provider sorts first, so old ids moved"
    assert flow.problems() == {}


def test_a_provider_removed_leaves_no_stale_entry_and_asks_nothing(flow):
    flow.add_provider()
    flow.run()
    asked = flow.calls()
    flow.remove_provider()
    lines = flow.run()
    doc = read_json(flow.paths.groups)
    assert flow.calls() == asked and flow.device_runs() == 2
    assert any("guide grouping: ok: rebuilt from the kept decisions" in line for line in lines)
    assert "Aaa" not in str(doc["items"]) and all(g["members"] for g in doc["groups"])
    assert sorted(m for g in doc["groups"] for m in g["members"]) == sorted(int(n) for n in doc["items"])
    assert "Aaa" not in flow.paths.knowledge.read_text() and flow.problems() == {}


def test_a_provider_added_back_asks_nothing(flow):
    flow.add_provider()
    flow.run()
    asked = flow.calls()
    groups = _group_by_name(flow.paths)
    flow.remove_provider()
    flow.run()
    flow.add_provider()
    flow.run()
    assert flow.calls() == asked and _group_by_name(flow.paths) == groups


@pytest.mark.parametrize("value", ["maybe", 1, [True]])
def test_a_malformed_no_rerun_warns_and_counts_as_true(flow, caplog, value):
    flow.run()
    flow.grouping = {"noRerun": value}
    with caplog.at_level(logging.WARNING, "perfrepair"):
        lines = flow.run()
    assert "guide grouping: ok: reused" in lines and flow.calls() == OLD_ITEMS
    assert any(m.startswith("invalid: device.grouping.noRerun ") and "true or false; using the default True" in m
               for m in caplog.messages)


def test_a_missing_no_rerun_warns_and_counts_as_true(flow, caplog):
    flow.run()
    flow.grouping = {}
    with caplog.at_level(logging.WARNING, "perfrepair"):
        lines = flow.run()
    assert "guide grouping: ok: reused" in lines and flow.calls() == OLD_ITEMS
    assert not any("noRerun" in m for m in caplog.messages if not m.startswith("setting "))


def test_knowledge_deleted_runs_anyway_with_no_rerun_true(flow):
    flow.run()
    shutil.rmtree(flow.paths.root / "outbox")
    lines = flow.run()
    assert f"guide grouping: ok: ran: {OLD_ITEMS} of {OLD_ITEMS} items asked" in lines and flow.calls() == 2 * OLD_ITEMS


def test_derived_files_deleted_are_rebuilt_with_no_call(flow):
    flow.run()
    flow.paths.knowledge.unlink()
    flow.paths.groups.unlink()
    lines = flow.run()
    assert any("rebuilt from the kept decisions" in line for line in lines) and flow.calls() == OLD_ITEMS
    assert flow.problems() == {}


def test_no_rerun_false_asks_every_item_into_a_new_outbox_and_keeps_the_old(flow):
    flow.run()
    old = active_fingerprint(flow.paths.root)
    flow.grouping = {"noRerun": False}
    lines = flow.run()
    new = active_fingerprint(flow.paths.root)
    assert flow.calls() == 2 * OLD_ITEMS and new != old and (flow.paths.root / "outbox" / old / "000001.json").is_file()
    assert f"guide grouping: ok: ran: device.grouping.noRerun false, all {OLD_ITEMS} items asked again" in lines
    assert flow.problems() == {}


def test_back_to_no_rerun_true_stays_on_the_refreshed_outbox(flow):
    flow.run()
    flow.grouping = {"noRerun": False}
    flow.run()
    new = active_fingerprint(flow.paths.root)
    flow.grouping = {"noRerun": True}
    lines = flow.run()
    assert "guide grouping: ok: reused" in lines and active_fingerprint(flow.paths.root) == new
    assert flow.calls() == 2 * OLD_ITEMS


def test_a_deleted_device_yaml_redoes_the_static_stages_and_still_asks_nothing(flow):
    flow.run()
    (flow.device / rd.DEVICE).unlink()
    assert "guide grouping: ok: reused" in flow.run() and flow.calls() == OLD_ITEMS
