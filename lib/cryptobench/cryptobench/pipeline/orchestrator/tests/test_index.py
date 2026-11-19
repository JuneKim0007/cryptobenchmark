import json

import yaml

from cryptobench.pipeline.orchestrator import index
from cryptobench.pipeline.orchestrator.summary import Row

FROM = {"testSet": "/s/tier1.yaml", "includes": [{"index": 0, "type": "Mac", "name": "HmacSHA256"}]}


def unit(tmp_path):
    folder = tmp_path / "results/pixel-10-api37-1a2b3c4d/tier1"
    (folder / "configuration").mkdir(parents=True)
    (folder / "preparation").mkdir()
    (folder / "benchmark").mkdir()
    (folder / "configuration/effective.yaml").write_text(yaml.safe_dump({"schemaVersion": 2, "providers": {
        "SunJCE": {"Mac": {"HmacSHA256": {"from": FROM}}}, "SUN": {"MessageDigest": {"SHA-256": {"from": {"testSet": "/s/tier1.yaml"}}}}}}))
    (folder / "configuration/report.yaml").write_text(yaml.safe_dump({"schemaVersion": 2, "skipped": [
        {"stage": "config", "provider": "BC", "type": "Mac", "name": "HmacSHA256", "code": "no_match", "reason": "nothing on this device matches the include"}]}))
    (folder / "preparation/prepared.yaml").write_text(yaml.safe_dump({"schemaVersion": 3, "cases": [
        {"id": "Mac_HmacSHA256_MAC_SunJCE_k256_i64_WARM_fixed", "from": FROM},
        {"id": "Mac_HmacSHA256_MAC_SunJCE_k256_i64_WARM_notFixed", "from": FROM}]}))
    (folder / "preparation/skipped.yaml").write_text(yaml.safe_dump({"schemaVersion": 2, "skipped": [
        {"stage": "preparation", "provider": "SUN", "type": "MessageDigest", "name": "SHA-256",
         "caseId": "MessageDigest_SHA-256_DIGEST_SUN_i64_WARM_fixed", "code": "unsupported_parameter", "reason": "x"}]}))
    (folder / "benchmark/benchmark.json").write_text(json.dumps({"cases": [
        {"id": "Mac_HmacSHA256_MAC_SunJCE_k256_i64_WARM_fixed", "metrics": {"timeNs": {"runs": [1.0, 2.0, 3.0]}}}]}))
    return folder


def test_every_case_of_a_run_is_listed_with_its_tier_device_state_runs_and_origin(tmp_path):
    folder = unit(tmp_path)
    cases = index.run_cases(Row("pixel10", "tier1", "finished", None, str(folder)), folder)
    base = {"suite": "tier1", "device": "pixel-10-api37-1a2b3c4d", "target": "pixel10"}
    assert cases == [
        {"id": "Mac_HmacSHA256_MAC_SunJCE_k256_i64_WARM_fixed", **base, "configured": True, "prepared": True, "skip": None, "runs": 3, "from": FROM},
        {"id": "Mac_HmacSHA256_MAC_SunJCE_k256_i64_WARM_notFixed", **base, "configured": True, "prepared": True, "skip": None, "runs": 0, "from": FROM},
        {"id": "MessageDigest_SHA-256_DIGEST_SUN_i64_WARM_fixed", **base, "configured": True, "prepared": False, "skip": "unsupported_parameter",
         "runs": 0, "from": {"testSet": "/s/tier1.yaml"}},
        {"id": None, "entry": "BC.Mac.HmacSHA256", **base, "configured": False, "prepared": False, "skip": "no_match", "runs": 0, "from": None}]


def test_a_run_that_wrote_nothing_has_no_cases_and_a_row_without_results_is_listed_alone(tmp_path):
    assert index.run_cases(Row("a", "tier1", "failed", "device_lost", str(tmp_path / "none")), tmp_path / "none") == []
    folder = unit(tmp_path)
    written = yaml.safe_load(index.written("s", [Row("a", "-", "skipped", "invalid_order"), Row("b", "tier1", "finished", None, str(folder))],
                                           tmp_path / "index.yaml").read_text())
    assert written["schemaVersion"] == 1 and written["session"] == "s"
    assert [r["state"] for r in written["runs"]] == ["skipped", "finished"] and {c["target"] for c in written["cases"]} == {"b"}
