import json
from pathlib import Path

import pytest

from perfrepair.data_handler.inbound import (
    build_run_log,
    comparability,
    manifest_file,
    read_manifest,
    read_prepared,
    read_probe_index,
    read_results,
    resolve,
    scan,
    summarise,
)
from perfrepair.data_handler.inbound.__main__ import main
from perfrepair.data_handler.inbound.run_log import (
    NO_SAMPLES,
    normalise_reason,
    split_case_id,
)
from perfrepair.dto import ProviderEntry, RunLog

F = Path(__file__).parent / "fixtures"
MANIFEST = F / "results" / "manifest.yaml"


@pytest.fixture
def run():
    manifest, base = read_manifest(MANIFEST)
    return manifest, base, (lambda key: manifest_file(manifest, base, key))


@pytest.fixture
def prepared(run):
    return read_prepared(run[2]("prepared"))


@pytest.fixture
def results(run, prepared):
    return read_results(run[2]("benchmark"), prepared)


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
        "schemaVersion: 1\nmode: host\nruntime: {}\nproviders: []\nfiles: {benchmark: benchmark/benchmark.json}\n")
    manifest, base = read_manifest(tmp_path / "manifest.yaml")
    with pytest.raises(FileNotFoundError):
        manifest_file(manifest, base, "benchmark")


def test_manifest_refuses_other_schema_versions(tmp_path):
    (tmp_path / "manifest.yaml").write_text("schemaVersion: 2\nmode: host\n")
    with pytest.raises(ValueError):
        read_manifest(tmp_path / "manifest.yaml")



def test_summary_statistics():
    s = summarise([1, 2, 3, 4, 5])
    assert (s.median, s.p25, s.p75, s.n) == (3, 2, 4, 5)
    with pytest.raises(ValueError):
        summarise([1, float("nan")])


def test_rows_join_phase_and_key_kind_from_prepared(results):
    rows, _ = results
    assert {r.rowId: (r.phase, r.keyKind) for r in rows} == {
        "g_fast": ("WARM", "secret"), "g_slow": ("WARM", "secret"), "d_fast": ("WARM", "none")}


def test_measurements_are_keyed_by_row_and_kept_apart_from_rows(results):
    rows, measurements = results
    assert set(measurements) == {r.rowId for r in rows}
    assert measurements["g_fast"]["timeNs"].median == 100
    assert measurements["g_fast"]["allocations"].median == 3
    assert measurements["g_slow"]["allocations"] is None


def test_comparability_from_runtime_and_process_count(run):
    notes = comparability(run[0].runtime, 1)
    assert any(n.startswith("cpu_not_locked") for n in notes)
    assert any(n.startswith("single_process") for n in notes)
    assert not any(n.startswith("single_process") for n in comparability({"cpuLocked": "true"}, 3))



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


def test_run_log_round_trips(log):
    assert RunLog.from_json(json.loads(json.dumps(log[0].to_json()))) == log[0]



@pytest.fixture
def index(run):
    return read_probe_index(run[2]("probe"))


def test_engine_types_come_from_the_probe(index):
    assert index.engine_types == {"Cipher", "MessageDigest", "Mac"}


def test_aliases_and_case_resolve_to_the_registered_name(index):
    assert index.canonical("Fast", "MessageDigest", "sha256") == "SHA-256"
    assert index.canonical("Fast", "Mac", "HmacSHA256") is None


def test_scan_finds_sites_and_ignores_build_dirs(index):
    sites = scan(F / "app", index.engine_types)
    assert [(s.engineType, s.line) for s in sites] == [
        ("Cipher", 12), ("MessageDigest", 17), ("Cipher", 21), ("Mac", 25), ("Cipher", 31)]
    assert sites[2].algorithm.literal is None and sites[2].algorithm.expr == "ALG"
    assert sites[2].provider.literal == "Fast"
    assert sites[3].provider.literal is None


def test_resolution_per_site(run, index):
    got = [resolve(s, index, run[0].providers) for s in scan(F / "app", index.engine_types)]
    assert [(s["resolvedProvider"], s["resolvedAlgorithm"], s["resolution"]) for s in got] == [
        ("Slow", "AES/GCM/NoPadding", "explicit"), ("Fast", "SHA-256", "default"),
        ("Fast", None, "unresolved_algorithm"), (None, None, "unresolved_provider"),
        ("Bundled", "AES/GCM/NoPadding", "provider_not_on_device")]


def test_default_resolution_follows_manifest_precedence(tmp_path, run, index):
    (tmp_path / "A.java").write_text('class A { Object c = Cipher.getInstance("aes/gcm/nopadding"); '
                                     'Object m = Mac.getInstance("HmacSHA256"); }')
    cipher, mac = scan(tmp_path, index.engine_types)
    flipped = [ProviderEntry("Slow", 1, 2), ProviderEntry("Fast", 2, 2)]
    assert resolve(cipher, index, run[0].providers)["resolvedProvider"] == "Fast"
    assert resolve(cipher, index, flipped)["resolvedProvider"] == "Slow"
    assert resolve(mac, index, run[0].providers)["resolvedProvider"] == "Slow"
    assert resolve(cipher, index, run[0].providers)["resolvedAlgorithm"] == "AES/GCM/NoPadding"



def test_command_writes_the_run_directory(tmp_path, capsys):
    assert main(["--manifest", str(MANIFEST), "--app", str(F / "app"), "-o", str(tmp_path)]) == 0
    docs = {n: json.loads((tmp_path / f"{n}.json").read_text()) for n in ("rows", "measurements", "run_log", "sites")}
    assert {n: d["schemaVersion"] for n, d in docs.items()} == {"rows": 1, "measurements": 2, "run_log": 1, "sites": 1}
    assert len(docs["rows"]["rows"]) == 3
    assert docs["measurements"]["measurements"]["g_fast"]["timeNs"]["median"] == 100
    assert len(docs["sites"]["sites"]) == 5
    out = capsys.readouterr().out
    assert "3 rows" in out and "warning cpu_not_locked" in out


def test_command_without_app_writes_no_sites(tmp_path):
    assert main(["--manifest", str(MANIFEST), "-o", str(tmp_path)]) == 0
    assert not (tmp_path / "sites.json").exists()


def test_measurements_document_round_trips(tmp_path):
    from perfrepair.dto import Measurements, Summary
    m = Measurements({"model": "x"}, ["note"], {"r1": {"timeNs": Summary(2, 1, 3, 0.1, 5, 1, 3), "allocations": None}})
    assert Measurements.from_json(json.loads(json.dumps(m.to_json()))) == m
