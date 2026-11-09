import json
from pathlib import Path

import pytest

from perfrepair.data_handler.inbound import (
    Probe,
    build_run_log,
    comparability,
    manifest_file,
    read_manifest,
    read_prepared,
    read_results,
    summarise,
)
from perfrepair.data_handler.inbound.__main__ import main
from perfrepair.data_handler.inbound.run_log import (
    NO_SAMPLES,
    normalise_reason,
    split_case_id,
)
from perfrepair.data_handler.inbound.results import ended_throttled, thermal_of
from perfrepair.dto import Measurements
from perfrepair.validation.rows import validate_rows
from helpers import row, with_results

F = Path(__file__).parent / "fixtures"
MANIFEST = F / "results" / "test-api36-00000000" / "manifest.yaml"


@pytest.fixture
def run():
    manifest, base = read_manifest(MANIFEST)
    return manifest, base, (lambda key: manifest_file(manifest, base, key))


@pytest.fixture
def prepared(run):
    return read_prepared(run[2]("prepared"))


@pytest.fixture
def results(run, prepared):
    return read_results(run[2]("benchmark"), prepared)[:2]


@pytest.fixture
def log(run, results, prepared):
    return build_run_log(results[0], prepared, run[2]("skipped"), run[2]("inventory"))



def test_manifest_paths_resolve_against_its_own_directory(run):
    manifest, base, path = run
    assert base == MANIFEST.parent.resolve()
    assert path("benchmark") == (MANIFEST.parent / "benchmark" / "benchmark.json").resolve()
    assert path("processes") is None
    assert [p.name for p in manifest.providers] == ["Fast", "Slow"]


def test_manifest_listing_a_missing_file_is_an_error(tmp_path):
    (tmp_path / "manifest.yaml").write_text(
        "schemaVersion: 1\nmode: host\ndeviceId: d\nruntime: {}\nproviders: []\nfiles: {benchmark: benchmark/benchmark.json}\n")
    manifest, base = read_manifest(tmp_path / "manifest.yaml")
    with pytest.raises(FileNotFoundError):
        manifest_file(manifest, base, "benchmark")


def test_a_manifest_from_before_device_ids_is_one_coded_line(tmp_path):
    (tmp_path / "manifest.yaml").write_text("schemaVersion: 1\nmode: host\nfiles: {}\n")
    with pytest.raises(ValueError, match=r"^manifest_without_device_id; rerun the benchmark$"):
        read_manifest(tmp_path / "manifest.yaml")


def test_manifest_refuses_other_schema_versions(tmp_path):
    (tmp_path / "manifest.yaml").write_text("schemaVersion: 2\nmode: host\n")
    with pytest.raises(ValueError):
        read_manifest(tmp_path / "manifest.yaml")



def test_summary_statistics():
    s = summarise([[1, 2, 3, 4, 5]])
    assert (s.median, s.p25, s.p75, s.n) == (3, 2, 4, 5)
    with pytest.raises(ValueError):
        summarise([[1, float("nan")]])


def test_rows_join_phase_and_key_kind_from_prepared(results):
    rows, _ = results
    assert {r.rowId: (r.phase, r.keyKind) for r in rows} == {
        "g_fast": ("WARM", "secret"), "g_slow": ("WARM", "secret"), "d_fast": ("WARM", "none")}


def test_measurements_are_keyed_by_row_and_kept_apart_from_rows(results):
    rows, measurements = results
    assert set(measurements) == {r.rowId for r in rows}
    assert measurements["g_fast"]["timeNs"].median == 100
    assert measurements["g_fast"]["allocationCount"].median == 3
    assert "allocationCount" not in measurements["g_slow"]


def test_a_case_carries_its_variant_and_one_without_is_the_legacy_notfixed(tmp_path, run, prepared):
    doc = json.loads(run[2]("benchmark").read_text())
    doc["cases"][0]["variant"] = "fixed"
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps(doc))
    rows = read_results(path, prepared)[0]
    assert {r.rowId: r.variant for r in rows} == {"g_fast": "fixed", "g_slow": "notFixed", "d_fast": "notFixed"}
    doc["cases"][1]["variant"] = None
    path.write_text(json.dumps(doc))
    from perfrepair.validation.rows import validate_rows
    [problem] = validate_rows(read_results(path, prepared)[0])
    assert problem.startswith("g_slow: variant")


def test_the_rows_validator_refuses_a_variant_outside_the_two():
    from dataclasses import replace
    from helpers import row
    from perfrepair.validation.rows import validate_rows
    assert [p.split(" ")[1] for p in validate_rows([replace(row("a", "P1"), variant="warm")])] == ["variant"]
    assert [p.split(" ")[1] for p in validate_rows([replace(row("a", "P1"), keySize=True)])] == ["keySize"]


def test_rows_of_an_older_schema_are_unreadable_so_the_device_stage_reruns_inbound(tmp_path):
    from perfrepair import run_dir as rd
    (tmp_path / rd.ROWS).write_text(json.dumps({"schemaVersion": 1, "rows": []}))
    with pytest.raises(ValueError, match="rows schemaVersion 1 is not 2"):
        rd.load_rows(tmp_path)


def test_comparability_from_runtime_and_process_count(run):
    notes = comparability(run[0].runtime, 1)
    assert any(n.startswith("cpu_not_locked") for n in notes)
    assert any(n.startswith("single_process") for n in notes)
    assert not any(n.startswith("single_process") for n in comparability({"cpuLocked": "true"}, 3))



def _without_time(tmp_path, settings=""):
    device = with_results(tmp_path / "d")
    path = device / "benchmark" / "benchmark.json"
    doc = json.loads(path.read_text())
    del doc["cases"][0]["metrics"]["timeNs"]
    path.write_text(json.dumps(doc))
    (tmp_path / "perfrepair.yaml").write_text(settings)
    return device, main(["--device-results", str(device), "--perfrepair-config", str(tmp_path / "perfrepair.yaml")])


def test_a_case_without_a_required_metric_is_skipped_counted_and_named(tmp_path):
    device, code = _without_time(tmp_path)
    log = json.loads((device / "run_log.json").read_text())["entries"]
    assert code == 0 and [e["rowIds"] for e in log if e["reason"] and e["reason"].startswith("no_required_metric:")] == [
        ["g_fast"]]
    assert all(r["rowId"] != "g_fast" for r in json.loads((device / "rows.json").read_text())["rows"])
    assert "no_required_metric" in (device / "log" / "status.log").read_text()


def test_stops_no_required_metric_stop_refuses_before_writing(tmp_path):
    device, code = _without_time(tmp_path, "stops: {no_required_metric: stop}\n")
    assert code == 1 and not (device / "rows.json").exists()


def test_case_id_is_split_out_of_a_reason():
    assert split_case_id("Cipher_X_k192_p81667fe4: dry_run_failed: Bad: 24 bytes") == (
        "Cipher_X_k192_p81667fe4", "dry_run_failed: Bad: 24 bytes")
    assert split_case_id("provider_not_installed: Foo") == (None, "provider_not_installed: Foo")
    assert split_case_id("not_positive: iterations 0") == (None, "not_positive: iterations 0")
    assert normalise_reason("Key: Spec@9b4f8de3\n  more") == "Key: Spec@… more"


def test_run_log_folds_identical_records(log):
    entries, raw = log
    assert raw == 3 + 1 + 3 + 1
    by = {(e.status, e.provider, e.type, e.reason): e for e in entries.entries}
    dry = by[("skipped", "Slow", "Mac", "dry_run_failed: BadKey: size 24")]
    assert dry.occurrences == 2 and dry.stage == "preparation"
    assert dry.rowIds == ("Mac_HmacSHA256_MAC_Slow_i1024_WARM_p0a1b2c3d", "Mac_HmacSHA256_MAC_Slow_i64_WARM_p0a1b2c3d")
    assert by[("skipped", "Slow", "Mac", "input_preparation_failed: no IV")].occurrences == 1
    assert by[("not_runnable", "Slow", "Mac", "BadKey: only store keys. Key: Spec@…")].stage == "trial"
    assert by[("unmeasured", "Slow", "MessageDigest", NO_SAMPLES)].rowIds == ("d_slow",)
    measured = [e for e in entries.entries if e.status == "measured"]
    assert sorted((e.provider, e.algorithm, e.occurrences) for e in measured) == [
        ("Fast", "AES/GCM/NoPadding", 1), ("Fast", "SHA-256", 1), ("Slow", "AES/GCM/NoPadding", 1)]
    assert sum(e.occurrences for e in entries.entries) == raw


@pytest.fixture
def index(run):
    return Probe.load(run[2]("probe")).index


def test_aliases_and_case_resolve_to_the_registered_name(index):
    assert index.registered("Fast", "MessageDigest", "sha256") == "SHA-256"
    assert index.registered("Fast", "Mac", "HmacSHA256") is None


def _probe(*services):
    return Probe({"schemaVersion": 1, "providers": [
        {"name": p, "services": [{"type": t, "algorithm": a, **extra}]} for p, t, a, extra in services]})


def test_a_site_lands_on_the_spelling_the_trial_composes_from_what_the_provider_declares():
    aes = {"attributes": {"SupportedModes": ["CBC"], "SupportedPaddings": ["PKCS5PADDING"]}}
    index = _probe(("P", "Cipher", "AES", aes), ("Q", "Cipher", "AES", {})).index
    assert index.registered("P", "Cipher", "AES/CBC/PKCS5Padding") == "AES/CBC/PKCS5PADDING"
    assert index.registered("Q", "Cipher", "AES/CBC/PKCS5Padding") == "AES/CBC/PKCS5Padding"


def test_a_transformation_resolves_through_the_base_service_like_jca():
    aes = {"attributes": {"SupportedModes": ["CBC", "ECB"], "SupportedPaddings": ["NoPadding", "PKCS5Padding"]}}
    index = _probe(("P", "Cipher", "AES", aes), ("P", "Cipher", "DES", {}),
                   ("P", "Cipher", "AES/GCM/NoPadding", {})).index
    assert index.registered("P", "Cipher", "AES/CBC/PKCS5PADDING") == "AES/CBC/PKCS5Padding"
    assert index.registered("P", "Cipher", "aes/gcm/nopadding") == "AES/GCM/NoPadding"
    assert index.registered("P", "Cipher", "DES/CBC/PKCS5Padding") == "DES/CBC/PKCS5Padding"
    assert index.registered("P", "Cipher", "AES/OFB/NoPadding") is None
    assert index.registered("P", "Cipher", "AES/CBC/PKCS7Padding") is None
    assert index.registered("P", "Mac", "AES/CBC/NoPadding") is None


def test_a_generator_service_gives_the_key_kind_it_makes():
    from cryptobench.catalogue.names import Names
    probe = _probe(("P", "KeyGenerator", "KS", {"aliases": ["ks-alias"]}), ("P", "KeyPairGenerator", "KP", {}))
    kind = probe.generator_kind(probe.names(Names.load()))
    assert (kind("ks-alias"), kind("KP"), kind("other")) == ("secret", "pair", None)


def test_command_writes_the_run_directory(tmp_path):
    assert main(["--device-results", str(with_results(tmp_path))]) == 0
    docs = {n: json.loads((tmp_path / f"{n}.json").read_text()) for n in ("rows", "measurements", "run_log")}
    assert len(docs["rows"]["rows"]) == 3
    assert docs["measurements"]["measurements"]["g_fast"]["timeNs"]["median"] == 100
    assert not (tmp_path / "sites.json").exists()


def test_thermal_blocks_join_measurements_and_only_ended_throttled_cases_are_named():
    hot = {"start": {"BIG": 40.0}, "end": {"BIG": 50.0}, "startStatus": 0, "endStatus": 2}
    cool = {**hot, "endStatus": 0}
    cases = [{"id": "a", "thermal": hot, "thermalThrottleSleepSeconds": 90}, {"id": "b", "thermal": cool}, {"id": "c"}]
    thermal = thermal_of(cases)
    assert thermal == {"a": {"thermal": hot, "thermalThrottleSleepSeconds": 90}, "b": {"thermal": cool}}
    assert ended_throttled(thermal) == ["a"]
    kept = Measurements({}, [], {}, thermal)
    assert Measurements.from_json(kept.to_json()).thermal == thermal and "thermal" not in Measurements({}, []).to_json()


def test_a_case_without_a_variant_is_refused():
    assert validate_rows([row("a", "P", variant=None)]) == ["a: variant None is not one of ('fixed', 'notFixed')"]
