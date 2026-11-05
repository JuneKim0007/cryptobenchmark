"""One device folder every AI role can run on, and per role how to run it, a right answer and one citing an id not shown."""
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from helpers import LATENCY, LIBRARY, QUIET, with_results
from site_replace_data import APP as REPLACE_APP, KEEP, answer, doc, dossier, member
from test_stages import F, first_improving_pair, same_name
from test_upgrade import APP as UPGRADE_APP, _doc as upgrade_doc, _family, Upgrades

from perfrepair import run_dir as rd
from perfrepair.ai.evaluate.worthiness.command import worthiness
from perfrepair.ai.parse.algorithm_classify.command import Reviewer, classify
from perfrepair.ai.parse.algorithm_classify.kind import ClassifyKind
from perfrepair.ai.parse.grouping_assign.command import assign
from perfrepair.ai.repair.upgrade.command import upgrade
from perfrepair.ai.review.grouping_review.command import review
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.kind import rebuild_problems
from perfrepair.ai.runtime.engine.outbox import active_outbox
from perfrepair.ai.suggest.site_replace.command import replace
from perfrepair.check.apps import check_repair, check_stability
from perfrepair.check.grouping import check_grouping, check_supervisor, check_worthiness
from perfrepair.data_handler.inbound.__main__ import main as inbound
from perfrepair.dto.classify import Batch, Evidence, read_batches
from perfrepair.dto.screen import UNKNOWN, Verdict
from perfrepair.files import read_json
from perfrepair.grouping.build.stage import build_stage
from perfrepair.grouping.report.checks import report
from perfrepair.review.stability import stability
from perfrepair.run_dir import AppPaths, GroupingPaths
from perfrepair.screen.catalog import screening_catalog
from perfrepair.validation.grouping.output import read_groups


def evidence(n):
    return Evidence(n, "TypeA", f"ALG-{n}", f"ALG-{n}", "P1", "fam", True, None, "a.B", {})


BATCHES = [Batch((evidence(3), evidence(4)))]
VERDICTS = {n: Verdict(UNKNOWN, "no screening row", None, f"ALG-{n}", None) for n in (3, 4)}


def _classify(device, conversations):
    classify(GroupingPaths(device), BATCHES, VERDICTS, Reviewer(conversations, LIBRARY), **QUIET)


def _classify_replay(device):
    paths = GroupingPaths(device)
    kind = ClassifyKind(read_batches(read_json(paths.classify_batches)), paths)
    return rebuild_problems(kind, active_outbox(paths.classify).records())


def _assign(device, conversations):
    assign(GroupingPaths(device), conversations, LIBRARY)


def _review(device, conversations):
    review(GroupingPaths(device), conversations, LIBRARY, **QUIET)


def _supervisor_replay(device):
    return [p for found in check_supervisor(GroupingPaths(device)).values() for p in found]


def _worthiness(device, conversations):
    worthiness(device, LATENCY, conversations, LIBRARY, **QUIET)


def _worthiness_replay(device):
    grouping = GroupingPaths(device)
    return check_worthiness(device, LATENCY.name, read_groups(grouping), rd.load_rows(device), rd.load_screen(grouping))


def _replace(device, conversations):
    replace(device, REPLACE_APP, conversations, LIBRARY, **QUIET)


def _replace_replay(device):
    return check_repair(device)[f"{REPLACE_APP}/{rd.REPLACEMENTS}"]


def _upgrade(device, conversations):
    upgrade(device, UPGRADE_APP, conversations, LIBRARY, **QUIET)


def _upgrade_replay(device):
    return check_repair(device)[f"{UPGRADE_APP}/{rd.UPGRADES}"]


def _stability(device, conversations):
    stability(device, conversations, LIBRARY, sample=5, asks=2)


def _stability_replay(device):
    return check_stability(device)[f"{rd.REVIEW}/stability.json"]


def _first_group(_task, *_):
    return {"group": "ghost-group", "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "not in the message"}


@dataclass(frozen=True)
class Role:
    name: str
    names: dict
    run: Callable
    right: Callable
    wrong_id: Callable
    replay: Callable
    files: Callable
    cited: str
    base: str = "assigned"


ROLES = (
    Role("screening.classify", {}, _classify,
         lambda *_: {"answers": [{"id": i, "answer": "unsure", "reason": "r"} for i in (3, 4)]},
         lambda *_: {"answers": [{"id": 3, "answer": "unsure", "reason": "r"}, {"id": 99, "answer": "unsure", "reason": "r"}]},
         _classify_replay, lambda d: [GroupingPaths(d).classified], "id 99"),
    Role("grouping.assign", {}, _assign, same_name, _first_group,
         lambda d: check_grouping(GroupingPaths(d)), lambda d: [GroupingPaths(d).knowledge, GroupingPaths(d).cursor], "ghost-group", "built"),
    Role("grouping.supervisor", {}, _review, lambda *_: {"findings": []},
         lambda *_: {"findings": [{"kind": "describe", "groups": ["ghost-group"], "items": [], "reason": "r"}]},
         _supervisor_replay, lambda d: [GroupingPaths(d).supervisor], "ghost-group"),
    Role("worthiness", {"mode": LATENCY.name}, _worthiness, first_improving_pair,
         lambda *_: {"decision": "test", "pairs": [{"from": "M99", "to": "M1", "reason": "r"}], "reason": "r"},
         _worthiness_replay, lambda d: [rd.worthiness(d, LATENCY.name) / rd.VERDICTS], "members"),
    Role("apps.replace", {"app": REPLACE_APP}, _replace, lambda *_: KEEP,
         lambda *_: {**answer(), "members": [member("S9")]}, _replace_replay, lambda d: [AppPaths(d, REPLACE_APP).replacements], "S9"),
    Role("repair-upgrade", {"app": UPGRADE_APP}, _upgrade, lambda *_: {"option": "R1", "reason": "fits"},
         lambda *_: {"option": "R99", "reason": "fits"}, _upgrade_replay, lambda d: [AppPaths(d, UPGRADE_APP).upgrades], "R99"),
    Role("review.stability", {}, _stability, lambda *_: KEEP,
         lambda *_: {**answer(), "members": [member("S9")]}, _stability_replay, lambda d: [rd.review_stability(d)], "S9"),
)


def _apps(device: Path) -> None:
    for app, document in ((REPLACE_APP, doc(dossier())),
                          (UPGRADE_APP, upgrade_doc(device, family=_family(listed=Upgrades({}))))):
        folder = device / app
        folder.mkdir()
        (folder / rd.APP).write_text(json.dumps({"root": "."}))
        (folder / rd.DOSSIERS).write_text(json.dumps(document))


def built_device(folder: Path) -> Path:
    assert inbound(["--device-results", str(with_results(folder))]) == 0
    build_stage(F, folder, screening_catalog(None), **QUIET)
    _apps(folder)
    return folder


def assigned_device(built: Path, folder: Path) -> Path:
    shutil.copytree(built, folder, dirs_exist_ok=True)
    assign(GroupingPaths(folder), ScriptedConversations(same_name), LIBRARY)
    report(GroupingPaths(folder))
    return folder
