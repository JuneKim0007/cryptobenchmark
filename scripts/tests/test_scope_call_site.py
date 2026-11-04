"""Call-site measurement: every swap's current and option item as prepared benchmark cases, whether or not its function compiles."""
import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import gradle_runner
from scope import call_site as scope_call_site
from scope import generate as scope_generate
from scope import results as scope_results
from session import measure as measure_session

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures/scoped"
EFFECTIVE = {"run": {"inputSizes": [64, 1024], "phases": ["WARM", "COLD"], "variants": ["fixed", "notFixed"], "metrics": ["TIME"],
                     "harness": {"iterations": 5}},
             "policy": {"onFailure": "stop"},
             "providers": {"BC": {"Cipher": {"AES/GCM/NoPadding": {"keySizes": [128, 256]}}, "MessageDigest": {"SHA-256": {}}},
                           "AndroidOpenSSL": {"Cipher": {"AES/GCM/NoPadding@iv": {"keySizes": [256], "parameters": {"x": 1}}},
                                              "MessageDigest": {"SHA-256": {}}}}}


def plan(tmp_path, harness="harness.yaml", compiler=lambda root: []):
    path, _ = scope_generate.generate(FIXTURES / harness, tmp_path / "root", tmp_path / "out", compiler=compiler)
    return yaml.safe_load(path.read_text())


def test_every_swap_with_one_operation_plans_both_sides_even_when_its_function_does_not_compile(tmp_path):
    failing = lambda root: [f"{scope_generate.GENERATED_MARK}x.java:1: error: no"]
    scopes = {s["id"]: s for s in plan(tmp_path, compiler=failing)["scopes"]}
    assert all(s["status"] == "not_compilable" for s in scopes.values())
    site = scopes["1b2c3d4e5f60"]["callSite"]
    assert site["status"] == "planned" and site["cases"] == ["scope:1b2c3d4e5f60:callSite:before", "scope:1b2c3d4e5f60:callSite:after"]
    assert site["sides"]["after"] == {"type": "Cipher", "algorithm": "AES/GCM/NoPadding", "provider": "AndroidOpenSSL",
                                      "keySize": 256, "inputSize": 1024}
    assert scopes["2c3d4e5f6071"]["callSite"]["variant"] == "fixed"
    assert (tmp_path / "root" / scope_generate.scope_wrapper.FOLDER / "GeneratedScopes.kt").read_text().count("listOf()") == 1


def test_a_scope_without_one_operation_or_a_callsite_is_not_measurable_with_its_reason(tmp_path):
    scopes = {s["id"]: s["callSite"] for s in plan(tmp_path, "broken.yaml")["scopes"]}
    assert scopes["2c3d4e5f6071"] == {"status": "not_measurable", "reason": "no_call_site: harness.yaml has no callSite"}


def written(tmp_path):
    effective = tmp_path / "effective.yaml"
    effective.write_text(yaml.safe_dump(EFFECTIVE))
    files = scope_call_site.write(scope_generate.call_sites(plan(tmp_path)), effective, tmp_path)
    return files, yaml.safe_load(files[0].read_text())["cases"]


def test_one_effective_per_distinct_selection_narrowed_to_the_operation_sizes_and_variant(tmp_path):
    files, cases = written(tmp_path)
    assert [f.name for f in files] == ["callsite.yaml"] + [f"callsite-{n}.yaml" for n in range(1, 7)]
    assert len(cases) == 6 and len({c["effective"] for c in cases}) == 6
    after = yaml.safe_load((tmp_path / next(c["effective"] for c in cases if c["id"] == "scope:1b2c3d4e5f60:callSite:after")).read_text())
    assert after["providers"] == {"AndroidOpenSSL": {"Cipher": {"AES/GCM/NoPadding@iv": {
        "keySizes": [256], "parameters": {"x": 1}, "operations": ["DECRYPT"], "inputSizes": [1024]}}}}
    assert (after["run"]["variants"], after["run"]["phases"], after["policy"]) == (["notFixed"], ["WARM"], {"onFailure": "skip"})
    digest = yaml.safe_load((tmp_path / next(c["effective"] for c in cases if c["id"] == "scope:2c3d4e5f6071:callSite:before")).read_text())
    assert digest["providers"] == {"BC": {"MessageDigest": {"SHA-256": {"operations": ["DIGEST"], "inputSizes": [1024]}}}}
    assert digest["run"]["variants"] == ["fixed"]


def test_nothing_planned_still_pushes_an_empty_plan_that_replaces_a_last_runs(tmp_path):
    effective = tmp_path / "effective.yaml"
    effective.write_text(yaml.safe_dump(EFFECTIVE))
    files = scope_call_site.write([], effective, tmp_path)
    assert [f.name for f in files] == ["callsite.yaml"] and yaml.safe_load(files[0].read_text())["cases"] == []


def test_each_call_sites_before_and_after_stay_a_pair_that_alternates_ab_ba():
    cases = ("scope:a:before", "scope:a:after", "scope:a:callSite:before", "scope:a:callSite:after")
    assert measure_session.alternating(2, cases) == ["scope:a:after", "scope:a:before", "scope:a:callSite:after", "scope:a:callSite:before"]


def test_two_scopes_on_one_selection_share_its_effective(tmp_path):
    folder = tmp_path / "h"
    folder.mkdir()
    for source in FIXTURES.iterdir():
        (folder / source.name).write_text(source.read_text())
    doc = yaml.safe_load((FIXTURES / "harness.yaml").read_text())
    doc["scopes"][1]["callSite"] = {"operation": "ENCRYPT", "variant": "notFixed"}
    (folder / "harness.yaml").write_text(yaml.safe_dump(doc))
    path, _ = scope_generate.generate(folder / "harness.yaml", tmp_path / "root", tmp_path / "out", compiler=lambda root: [])
    effective = tmp_path / "effective.yaml"
    effective.write_text(yaml.safe_dump(EFFECTIVE))
    files = scope_call_site.write(scope_generate.call_sites(yaml.safe_load(path.read_text())), effective, tmp_path)
    cases = yaml.safe_load(files[0].read_text())["cases"]
    assert len(cases) == 6 and len({c["effective"] for c in cases}) == 4


DEVICE_CASE = {"id": "Cipher_AES-GCM-NoPadding_DECRYPT_AndroidOpenSSL_k256_i1024_WARM_notFixed", "type": "Cipher",
               "algorithm": "AES/GCM/NoPadding", "provider": "AndroidOpenSSL", "operation": "DECRYPT", "chartGroup": "aead", "chartGroupId": 1,
               "keySize": 256, "inputSize": 1024, "phase": "WARM", "variant": "notFixed", "metrics": ["TIME"], "harness": {"iterations": 5},
               "key": {"kind": "secret", "algorithm": "AES", "provider": "AndroidOpenSSL", "keySize": 256, "encodedBytes": 32},
               "input": {"kind": "ciphertext", "bytes": 1040}, "fingerprint": "00000000", "resolvedParameters": {"tagBits": 128}}


def test_prepared_call_sites_join_the_session_beside_the_functions_and_convert_with_the_real_converter(tmp_path):
    record = plan(tmp_path)
    (tmp_path / "scoped-plan.yaml").write_text(yaml.safe_dump(record))
    interop = tmp_path / "scoped-interop.yaml"
    interop.write_text("".join(f'"{s["id"]}": {{interop: passed, check: same_output}}\n' for s in record["scopes"]))
    folder = tmp_path / "callsite-1"
    folder.mkdir()
    (folder / "prepared.yaml").write_text(yaml.safe_dump({"cases": [DEVICE_CASE]}))
    sites = tmp_path / "callsite-verdicts.yaml"
    sites.write_text("".join(f'"{c}": {{status: prepared, folder: callsite-1, case: "{DEVICE_CASE["id"]}"}}\n'
                             for s in record["scopes"] for c in s["callSite"]["cases"] if s["id"] != "2c3d4e5f6071")
                     + '"scope:2c3d4e5f6071:callSite:before": {status: not_prepared, reason: "not_prepared: none"}\n')
    document, measured, call_sites = scope_results.merge(tmp_path / "scoped-plan.yaml", interop, sites)
    assert [r["id"] for r in call_sites] == ["0a1b2c3d4e5f", "1b2c3d4e5f60"]
    kept = {s["id"]: s["callSite"] for s in yaml.safe_load((tmp_path / "scoped-plan.yaml").read_text())["scopes"]}
    assert (kept["2c3d4e5f6071"]["status"], kept["2c3d4e5f6071"]["reason"]) == ("not_prepared", "not_prepared: none")
    cases = scope_results.cases_of(measured, call_sites)
    assert cases[-4:] == ("scope:0a1b2c3d4e5f:callSite:before", "scope:0a1b2c3d4e5f:callSite:after",
                          "scope:1b2c3d4e5f60:callSite:before", "scope:1b2c3d4e5f60:callSite:after")
    effective = tmp_path / "effective.yaml"
    effective.write_text("run: {metrics: [TIME], harness: {iterations: 3}}\n")
    prepared = scope_results.prepared(document, measured, effective, tmp_path / "prepared.yaml", call_sites)
    entry = next(c for c in yaml.safe_load(prepared.read_text())["cases"] if c["id"] == "scope:1b2c3d4e5f60:callSite:after")
    assert (entry["type"], entry["operation"], entry["variant"], entry["harness"]) == ("Cipher", "DECRYPT", "notFixed", {"iterations": 3})
    data = tmp_path / "benchmarkData.json"
    benchmark = lambda c: {"name": f"measure[{c}]", "repeatIterations": 10, "thermalThrottleSleepSeconds": 0, "metrics": {
        "timeNs": {"minimum": 5.0, "maximum": 5.0, "median": 5.0, "coefficientOfVariation": 0.0, "runs": [5.0] * 3}}}
    data.write_text(json.dumps({"context": {"build": {"model": "fake", "fingerprint": "f", "version": {"sdk": 36}}, "cpuLocked": False,
                                            "sustainedPerformanceModeEnabled": False, "compilationMode": "speed"},
                                "benchmarks": [benchmark(c) for c in cases]}))
    gradle_runner.run(f"{data} {prepared} {tmp_path}", False, main_class="ConvertKt")
    converted = {c["id"]: c for c in json.loads((tmp_path / "benchmark.json").read_text())["cases"]}
    assert set(converted) == set(cases) and converted["scope:1b2c3d4e5f60:callSite:after"]["operation"] == "DECRYPT"
