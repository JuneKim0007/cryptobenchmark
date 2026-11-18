"""Block ranges, identity differences and the partial move-aside a resumed publish makes."""
import pathlib, types

from cryptobench.shared.results import identity, layout
from cryptobench.stages.measurement.session import blocks


def test_runs_split_into_blocks_of_k_the_last_one_shorter():
    assert blocks.ranges(7, 2) == [(1, 1, 2), (2, 3, 4), (3, 5, 6), (4, 7, 7)]
    assert blocks.ranges(3, 10) == [(1, 1, 3)]
    assert blocks.ranges(3, 1) == [(1, 1, 1), (2, 2, 2), (3, 3, 3)]


def test_a_changed_identity_names_run_and_device_keys_by_their_dotted_name():
    before = {"schema": 1, "run": {"seed": 0, "launchRetries": 2}, "selection": "s", "code": "c", "device": {"release": "16"}, "order": {"scheme": "i"}}
    after = {**before, "run": {"seed": 1, "launchRetries": 2, "warmup": {}}, "code": "d", "device": {"release": "17"}}
    assert identity.changed(before, after) == ["code", "device.release", "run.seed", "run.warmup"]
    assert identity.changed(before, dict(before)) == []


def test_the_timed_code_digest_covers_every_pattern():
    assert len(identity.timed_code()) == 64


def test_a_runner_edit_changes_only_code_runner_and_bytecode_is_not_code(tmp_path):
    repo = types.SimpleNamespace(root=tmp_path, timed_code=("timed/*",), runner_code=("runner/**/*.py",))
    written(tmp_path / "timed/Bench.kt"), written(tmp_path / "runner/session/launch.py")
    before = identity.code(repo)
    written(tmp_path / "runner/session/__pycache__/launch.cpython-314.pyc", "compiled")
    assert identity.code(repo) == before
    written(tmp_path / "runner/session/launch.py", "edited")
    after = identity.code(repo)
    assert identity.changed({"code": before}, {"code": after}) == ["code.runner"]


def written(path, text="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_a_publish_keeps_the_kept_paths_in_place_and_moves_everything_beside_them(tmp_path, capsys):
    target = tmp_path / "device"
    for name in ("manifest.yaml", "configuration/effective.yaml", "benchmark/process-1/cases/a.json", "benchmark/process-2/cases/a.json",
                 "benchmark/blocks/block-1.yaml", "benchmark/benchmark.json"):
        written(target / name)
    kept = (pathlib.PurePosixPath("benchmark/process-1"), pathlib.PurePosixPath("benchmark/blocks/block-1.yaml"))
    into = layout.supersede(target, "keep", kept)
    left = sorted(p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file() and "superseded" not in p.parts)
    moved = sorted(p.relative_to(into).as_posix() for p in into.rglob("*") if p.is_file())
    assert left == ["benchmark/blocks/block-1.yaml", "benchmark/process-1/cases/a.json"]
    assert moved == ["benchmark/benchmark.json", "benchmark/process-2/cases/a.json", "configuration/effective.yaml", "manifest.yaml"]
    assert "run_superseded" in capsys.readouterr().out
