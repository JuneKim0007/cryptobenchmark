"""#78's flows across runs on the fake pipeline and the dry-run gateway: what reruns, how many device runs and model calls."""
import json
import logging
import shutil
from pathlib import Path

import pytest
import yaml
from helpers import model_calls

from cryptobench.paths import AppTree, GroupingTree, RunTree
from perfrepair import run_dir as rd
from perfrepair.ai.runtime.engine.outbox import active_fingerprint
from perfrepair.check.run import validate_run
from perfrepair.files import read_json
from cryptobench.catalogue import groups as group_catalog_file
from perfrepair.catalog import signature
from perfrepair.app.facts.path_id import path_id
from perfrepair.guide.command import main as guide
from perfrepair.screen.catalog import screening_catalog

F = Path(__file__).parent / "fixtures"
APP = F / "app"
FOLDER = "fake-api36-00000000"
BUNDLED_FIRST = "bundled: [{artifact: 'g:a:1', create: Aaa}]"
OLD_ITEMS = 4
INTERCHANGE = signature.interchange
GROUPS = group_catalog_file.CATALOG
pytestmark = pytest.mark.usefixtures("asked_by_model")


def _real_catalog(monkeypatch):
    """Undo asked_by_model for a test of what the catalog groups across providers."""
    monkeypatch.setattr(signature, "interchange", INTERCHANGE)
    monkeypatch.setattr(group_catalog_file, "CATALOG", GROUPS)
    group_catalog_file.group_catalog.cache_clear()


class Flow:
    def __init__(self, tmp_path, capsys):
        self.tmp, self.capsys = tmp_path, capsys
        self.root, self.global_yaml = tmp_path / "results", tmp_path / "global.yaml"
        self.device = self.root / FOLDER
        self.paths = GroupingTree(self.device)
        self.global_yaml.write_text("schemaVersion: 1\nselection: {testSet: x.yaml}\nproviders: {bundled: []}\n")
        self.grouping = {}
        self.filter = False
        self.bundled = {}
        self.stops = {}

    def settings(self, text=None):
        path = self.tmp / "perfrepair.yaml"
        document = {"device": {"grouping": self.grouping, "filterByApps": self.filter, "bundled": self.bundled},
                    "apps": {"perfMode": ["latency", "throughput"]}, "stops": self.stops}
        path.write_text(text if text is not None else yaml.safe_dump(document))
        return path

    def where(self):
        return ["--results-root", str(self.root), "--config", str(self.global_yaml)]

    def run(self, text=None):
        guide(["--app", str(APP), "--agent", "dry-run", "--perfrepair-config", str(self.settings(text)), *self.where()])
        return [line for line in self.capsys.readouterr().out.splitlines() if line.startswith(("device ", "guide "))]

    def calls(self):
        return model_calls(self.device, "grouping")

    def device_runs(self):
        log = self.root / "runs.log"
        return len(log.read_text().splitlines()) if log.is_file() else 0

    def add_provider(self):
        self.global_yaml.write_text(self.global_yaml.read_text().replace("bundled: []", BUNDLED_FIRST))

    def remove_provider(self):
        self.global_yaml.write_text(self.global_yaml.read_text().replace(BUNDLED_FIRST, "bundled: []"))

    def events(self):
        """The last run's events."""
        events = [json.loads(e) for e in (self.device / "log" / "events.jsonl").read_text().splitlines()]
        return [e for e in events if e["run"] == events[-1]["run"]]

    def ended(self, step, stage="device"):
        """A step's outcome and counts in the last run."""
        last = [e for e in self.events() if (e["stage"], e["step"], e["event"]) == (stage, step, "end")]
        return (last[-1]["outcome"], last[-1]["data"].get("counts", {})) if last else (None, {})

    def found(self, code):
        """The last run's findings of a code: step, outcome and items."""
        return [(e["step"], e["outcome"], e["data"].get("items")) for e in self.events()
                if e["event"] == "finding" and e["data"].get("code") == code]

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
    flow.run()
    assert flow.ended("grouping") == ("ran", {"items": OLD_ITEMS, "asked": OLD_ITEMS})
    assert flow.calls() == OLD_ITEMS and flow.device_runs() == 1 and flow.problems() == {}


def test_a_provider_added_asks_only_its_new_items_and_rebuilds_the_groups(flow):
    flow.run()
    kept = _group_by_name(flow.paths)
    outbox = active_fingerprint(flow.paths.root)
    ids_before = {e["qualified"]: n for n, e in read_json(flow.paths.groups)["items"].items()}
    flow.add_provider()
    flow.run()
    groups = _group_by_name(flow.paths)
    assert flow.device_runs() == 2 and active_fingerprint(flow.paths.root) == outbox
    # AES/GCM and SHA-256 of the new provider; its MD5 is screened out and grouped by code
    assert flow.calls() == OLD_ITEMS + 2 and flow.ended("grouping") == ("ran", {"items": OLD_ITEMS + 2, "asked": 2})
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
    flow.run()
    doc = read_json(flow.paths.groups)
    assert flow.calls() == asked and flow.device_runs() == 2 and flow.ended("grouping")[1]["asked"] == 0
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


def test_knowledge_deleted_runs_anyway(flow):
    flow.run()
    shutil.rmtree(flow.paths.root / "outbox")
    flow.run()
    assert flow.ended("grouping") == ("ran", {"items": OLD_ITEMS, "asked": OLD_ITEMS}) and flow.calls() == 2 * OLD_ITEMS


def test_derived_files_deleted_are_rebuilt_with_no_call(flow):
    flow.run()
    flow.paths.knowledge.unlink()
    flow.paths.groups.unlink()
    flow.run()
    assert flow.ended("grouping")[1]["asked"] == 0 and flow.calls() == OLD_ITEMS
    assert flow.problems() == {}


def test_a_deleted_device_yaml_keeps_the_measured_run_redoes_the_rest_and_asks_nothing(flow):
    flow.run()
    (RunTree(flow.device).device).unlink()
    flow.run()
    assert flow.ended("benchmark")[0] == "reused" and flow.ended("inbound")[0] == "ran" and flow.device_runs() == 1
    assert flow.ended("grouping")[0] == "reused" and flow.calls() == OLD_ITEMS and flow.problems() == {}


SHA = "MessageDigest|SHA-256|Fast"
HMAC = "Mac|HmacSHA256|Slow"
GCM_FAST, GCM_SLOW = "Cipher|AES/GCM/NoPadding|Fast", "Cipher|AES/GCM/NoPadding|Slow"
CALLS = {SHA: 'java.security.MessageDigest.getInstance("SHA-256")', HMAC: 'javax.crypto.Mac.getInstance("HmacSHA256")'}


def target(flow, name, *items, ships=""):
    """The demo app's build files around one class calling only these items; ships: one more dependency it declares."""
    root = flow.tmp / "apps" / name
    shutil.copytree(APP, root, ignore=shutil.ignore_patterns("java", "kotlin"))
    # one applicationId per target, else apps.targets merges them
    (root / "src/main/AndroidManifest.xml").write_text(f'<manifest package="demo.{name}" />')
    if ships:
        build = root / "build.gradle"
        build.write_text(build.read_text().replace("dependencies {", f"dependencies {{\n    implementation '{ships}'"))
    body = "\n".join(f"    Object m{n}() throws Exception {{ return {CALLS[q]}; }}" for n, q in enumerate(items))
    (root / "src/main/java/demo").mkdir(parents=True)
    (root / "src/main/java/demo/Uses.java").write_text(f"package demo;\n\nclass Uses {{\n{body}\n}}\n")
    return root


@pytest.fixture
def scoped(flow):
    flow.filter = True
    flow.sha, flow.hmac = target(flow, "sha", SHA), target(flow, "hmac", HMAC)
    return flow


def run_targets(flow, *roots, device=False):
    path = flow.settings()
    document = yaml.safe_load(path.read_text())
    document["apps"] = {"targets": [str(r) for r in roots], "perfMode": ["latency", "throughput"]}
    path.write_text(yaml.safe_dump(document))
    guide(["--agent", "dry-run", "--perfrepair-config", str(path), *flow.where(), *(("--device",) if device else ())])
    return [line for line in flow.capsys.readouterr().out.splitlines() if line.startswith(("device ", "guide "))]


def excluded(flow):
    return json.loads((flow.root / "excluded.log").read_text().splitlines()[-1])


def used(flow):
    return {u["item"]: u["via"] for u in read_json(RunTree(flow.device).used)["items"]}


def test_filter_a_first_target_groups_and_measures_only_what_it_uses(scoped):
    run_targets(scoped, scoped.sha)
    assert used(scoped) == {SHA: "site"} and scoped.calls() == 1 and scoped.device_runs() == 2
    assert scoped.ended("grouping") == ("ran", {"items": 1, "asked": 1, "notUsed": 3})
    assert excluded(scoped) == sorted([HMAC, GCM_FAST, GCM_SLOW])
    assert len(read_json(scoped.paths.groups)["notUsed"]) == 3 and scoped.problems() == {}


def test_filter_nothing_changed_is_no_call_no_device_run_and_grouping_reused(scoped):
    run_targets(scoped, scoped.sha)
    before = scoped.paths.groups.stat().st_mtime_ns
    run_targets(scoped, scoped.sha)
    assert scoped.ended("grouping")[0] == "reused" and scoped.calls() == 1 and scoped.device_runs() == 2
    assert scoped.ended("benchmark")[0] == "reused" and scoped.paths.groups.stat().st_mtime_ns == before


def test_filter_a_new_target_asks_only_its_new_items_and_reruns_no_benchmark_for_a_refused_one(scoped):
    run_targets(scoped, scoped.sha)
    run_targets(scoped, scoped.sha, scoped.hmac)
    # the used set grew by an item the preparation refused: a coded gap, no delta and no whole rerun
    assert scoped.calls() == 2 and scoped.device_runs() == 2 and scoped.ended("benchmark")[0] == "reused"
    coverage = yaml.safe_load((RunTree(scoped.device).log.benchmark_coverage).read_text())
    assert coverage["items"][HMAC] == "refused" and coverage["totals"]["refused"] == 1
    assert scoped.ended("grouping") == ("ran", {"items": 2, "asked": 1, "notUsed": 2})
    assert scoped.problems() == {}


def test_filter_a_target_removed_keeps_its_groups_and_rows_and_asks_nothing(scoped):
    run_targets(scoped, scoped.sha, scoped.hmac)
    kept = _group_by_name(scoped.paths)[SHA]
    run_targets(scoped, scoped.hmac)
    assert scoped.calls() == 2 and scoped.device_runs() == 2 and scoped.ended("benchmark")[0] == "reused"
    assert used(scoped) == {HMAC: "site"} and _group_by_name(scoped.paths)[SHA] == kept
    assert SHA in {f"{r['type']}|{r['algorithm']}|{r['provider']}" for r in read_json(RunTree(scoped.device).rows)["rows"]}
    record, _ = rd.load_device_record(scoped.device)
    assert set(record.benchmark["items"]) == {SHA, HMAC} and scoped.problems() == {}


def test_filter_off_asks_and_measures_every_item(scoped):
    run_targets(scoped, scoped.sha)
    scoped.filter = False
    run_targets(scoped, scoped.sha)
    assert scoped.calls() == OLD_ITEMS and scoped.device_runs() == 3 and excluded(scoped) == []
    assert not (RunTree(scoped.device).used).exists() and "notUsed" not in read_json(scoped.paths.groups)
    record, _ = rd.load_device_record(scoped.device)
    assert record.benchmark == {} and scoped.problems() == {}


CONSCRYPT = "org.conscrypt:conscrypt-android:2.5.2"


def suggestions(flow):
    return yaml.safe_load((RunTree(flow.device).bundled_suggestions).read_text())


def applied(flow):
    used = yaml.safe_load((RunTree(flow.device).used_config).read_text())
    return used["providers"]["bundled"]


def test_bundled_stop_halts_before_the_benchmark_naming_each_provider(scoped):
    scoped.stops = {"bundled_missing": "stop"}
    run_targets(scoped, scoped.sha)
    assert scoped.device_runs() == 1 and not (RunTree(scoped.device).used_config).exists()
    assert scoped.found("bundled_missing") == [("bundled", "stop", ["BC"])]


def test_bundled_warn_logs_and_the_run_goes_on(scoped):
    run_targets(scoped, scoped.sha)
    assert scoped.found("bundled_missing") == [("bundled", "warn", ["BC"])] and scoped.device_runs() == 2
    assert not (RunTree(scoped.device).bundled_suggestions).exists() and scoped.problems() == {}


def test_bundled_suggest_writes_the_matched_the_blocked_and_applies_nothing(scoped):
    scoped.bundled = {"fromApps": "suggest"}
    run_targets(scoped, target(scoped, "tls", SHA, ships=CONSCRYPT))
    doc = suggestions(scoped)
    assert [(s["provider"], s["entry"], s.get("applied")) for s in doc["matched"]] == [
        ("Conscrypt", {"artifact": CONSCRYPT, "create": "org.conscrypt.Conscrypt#newProvider", "alias": "BundledConscrypt"},
         False)]
    assert [(s["provider"], s["artifact"], s["version"]) for s in doc["blocked"]] == [
        ("BC", "org.bouncycastle:bcprov-jdk18on", "1.78")]
    assert "duplicate_name" in doc["blocked"][0]["reason"] and applied(scoped) == []
    assert scoped.problems() == {}


def test_bundled_apply_builds_the_matched_row_in_and_a_second_run_reuses_it(scoped):
    scoped.bundled = {"fromApps": "apply"}
    tls = target(scoped, "tls", SHA, ships=CONSCRYPT)
    run_targets(scoped, tls, device=True)
    assert applied(scoped) == [{"artifact": CONSCRYPT, "create": "org.conscrypt.Conscrypt#newProvider",
                                "alias": "BundledConscrypt"}]
    # the blocked BC is listed, never built in, so it is still missing
    # three runs: the first probe finds the apps, the second holds the applied provider, then the benchmark
    assert scoped.found("bundled_missing") == [("bundled", "warn", ["BC"])] and scoped.device_runs() == 3
    assert suggestions(scoped)["counts"]["applied"] == 1 and scoped.problems() == {}
    run_targets(scoped, tls, device=True)
    assert scoped.device_runs() == 3 and scoped.ended("probe")[0] == scoped.ended("benchmark")[0] == "reused"


def test_bundled_apply_turned_off_reruns_the_benchmark_on_the_base_set(scoped):
    scoped.bundled = {"fromApps": "apply"}
    tls = target(scoped, "tls", SHA, ships=CONSCRYPT)
    run_targets(scoped, tls, device=True)
    scoped.bundled = {}
    run_targets(scoped, tls, device=True)
    # the kept probe still holds the provider: probed again without it, then measured
    assert scoped.device_runs() == 5 and applied(scoped) == [] and scoped.ended("benchmark")[0] == "ran"
    record, _ = rd.load_device_record(scoped.device)
    assert record.bundled == {} and not (RunTree(scoped.device).bundled_config).exists()


def test_bundled_apply_measures_only_the_algorithms_the_sites_name_and_groups_them_with_the_platform(scoped, monkeypatch):
    _real_catalog(monkeypatch)
    scoped.bundled = {"fromApps": "apply"}
    run_targets(scoped, target(scoped, "tls", SHA, ships=CONSCRYPT), device=True)
    groups = read_json(scoped.paths.groups)
    names = {k: v["qualified"] for k, v in groups["items"].items()}
    members = [{names[str(m)] for m in g["members"]} for g in groups["groups"]]
    sha = next(m for m in members if "MessageDigest|SHA-256|BundledConscrypt" in m)
    assert {q.rsplit("|", 1)[1] for q in sha} - {"BundledConscrypt"}
    assert used(scoped)["MessageDigest|SHA-256|BundledConscrypt"] == "group"
    assert {"MessageDigest|MD5|BundledConscrypt", "Cipher|AES/GCM/NoPadding|BundledConscrypt"} <= set(excluded(scoped))
    assert "MessageDigest|SHA-256|BundledConscrypt" not in excluded(scoped)


def _sha_options(flow, root):
    doc = read_json(AppTree(flow.device, path_id(root)).dossiers)
    [d] = [d for d in doc["dossiers"] if d["current"].startswith("MessageDigest|SHA-256|")]
    return d["current"], {o["item"]: (o["track"], o["needsReview"]) for o in d["options"]}


@pytest.mark.parametrize("registers, current, offered", [
    (False, "MessageDigest|SHA-256|Fast", "MessageDigest|SHA-256|BundledConscrypt"),
    (True, "MessageDigest|SHA-256|BundledConscrypt", "MessageDigest|SHA-256|Fast")])
def test_a_shipped_provider_is_a_provider_path_in_both_directions(scoped, monkeypatch, registers, current, offered):
    _real_catalog(monkeypatch)
    scoped.bundled = {"fromApps": "apply"}
    root = target(scoped, "tls", SHA, ships=CONSCRYPT)
    if registers:
        (root / "src/main/java/demo/Boot.java").write_text(
            "package demo;\n\nimport java.security.Security;\nimport org.conscrypt.Conscrypt;\n\nclass Boot {\n"
            "    void boot() { Security.insertProviderAt(Conscrypt.newProvider(), 1); }\n}\n")
    run_targets(scoped, root, device=True)
    on, options = _sha_options(scoped, root)
    assert on == current and options[offered] == ("provider_path", ["resolved_by_order"])


@pytest.mark.parametrize("value", ["always", 1])
def test_a_bad_bundled_value_warns_and_takes_the_default(scoped, caplog, value):
    scoped.bundled = {"fromApps": value}
    with caplog.at_level(logging.WARNING, "perfrepair"):
        run_targets(scoped, scoped.sha)
    assert scoped.found("bundled_missing") == [("bundled", "warn", ["BC"])] and scoped.device_runs() == 2
    assert not (RunTree(scoped.device).bundled_suggestions).exists()
    assert {m.split(" ")[1] for m in caplog.messages if m.startswith("invalid: device.bundled.")} == {"device.bundled.fromApps"}


def _stage(flow, *flags):
    path = flow.settings()
    document = yaml.safe_load(path.read_text())
    document["apps"] = {"targets": [str(flow.sha)], "perfMode": ["latency", "throughput"]}
    path.write_text(yaml.safe_dump(document))
    outcome = flow.tmp / "outcome.json"
    code = guide(["--agent", "dry-run", "--perfrepair-config", str(path), "--config", str(flow.global_yaml), "--outcome", str(outcome), *flags])
    return code, json.loads(outcome.read_text())


def test_stop_after_device_measures_once_and_asks_no_model(scoped):
    code, outcome = _stage(scoped, "--results-root", str(scoped.root), "--stop-after-device", "--run-id", "one")
    assert code == 0 and scoped.device_runs() == 2 and scoped.calls() == 0
    assert not [e for e in scoped.events() if e["stage"] == "guide" and e["step"] in ("grouping", "targets", "app")]
    assert outcome == {"device": str(scoped.device), "run": "one", "exit": 0, "code": None}
    assert not scoped.paths.groups.exists()


def test_the_named_folder_after_it_groups_and_runs_the_apps_with_no_second_benchmark(scoped):
    _stage(scoped, "--results-root", str(scoped.root), "--stop-after-device", "--run-id", "one")
    code, outcome = _stage(scoped, "--device-results", str(scoped.device), "--run-id", "one", "--on-existing", "resume")
    assert scoped.device_runs() == 2 and scoped.calls() > 0 and scoped.paths.groups.is_file()
    assert scoped.ended("grouping")[0] == "ran" and scoped.ended("app", stage="guide")[0] == "ok"
    assert outcome["device"] == str(scoped.device) and outcome["run"] == "one" and outcome["exit"] == code


def test_a_failed_device_stage_gives_its_code(scoped, monkeypatch):
    monkeypatch.setenv("FAKE_INTERRUPT", "1")
    code, outcome = _stage(scoped, "--results-root", str(scoped.root), "--stop-after-device")
    assert code == 1 and outcome["exit"] == 1 and outcome["code"] == "pipeline_failed"


def test_a_bad_run_id_is_a_usage_error(scoped, capsys):
    with pytest.raises(SystemExit) as e:
        guide(["--app", str(APP), "--agent", "dry-run", "--run-id", "a/b"])
    assert e.value.code == 2 and "--run-id" in capsys.readouterr().err
