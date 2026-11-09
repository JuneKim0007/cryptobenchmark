import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from handoff_check import LAYERS, ROOT, check, owned_violations, violations  # noqa: E402

LAYERS_DOC = {
    "root": "io.x",
    "modules": {"prep": {}, "bench": {}, "lone": {}},
    "consumers": {
        "app": {"sources": "app", "uses": {"prep": ["Entry", "plan.Plan"], "bench": "all"}},
    },
}


def write(repo: pathlib.Path, body: str) -> None:
    path = repo / "app/io/x/Main.kt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def test_listed_and_all_pass_others_fail(tmp_path):
    write(tmp_path, "\n".join([
        "package io.x",
        "import io.x.prep.Entry",
        "import io.x.prep.plan.Plan as P",
        "import io.x.bench.run.Anything",
        "import io.x.prep.key.Secret",
        "import io.x.lone.*",
        "val c = io.x.prep.plan.Inner::class",
    ]))
    assert violations(LAYERS_DOC, tmp_path) == {
        "app: io/x/Main.kt -> prep.key.Secret",
        "app: io/x/Main.kt -> lone.*",
        "app: io/x/Main.kt -> prep.plan.Inner",
    }


def test_frozen_entries_pass_new_and_fixed_fail(tmp_path):
    frozen = tmp_path / "frozen.txt"
    frozen.write_text("kept\nfixed\n")
    assert check({"kept", "added"}, frozen, shrink=False) == ["new: added", "fixed, remove from frozen.txt (--shrink): fixed"]


def test_shrink_drops_fixed_and_never_adds(tmp_path):
    frozen = tmp_path / "frozen.txt"
    frozen.write_text("kept\nfixed\n")
    assert check({"kept", "added"}, frozen, shrink=True) == ["new: added"]
    assert frozen.read_text() == "kept\n"


def test_repository_matches_its_frozen_list():
    found = violations(yaml.safe_load(LAYERS.read_text()), ROOT)
    assert check(found, LAYERS.parent / "handoff-frozen.txt", shrink=False) == []


def test_an_entry_point_named_outside_its_owner_fails_and_a_comment_does_not(tmp_path):
    layers = {"owned": {"sources": "src", "entries": {"BenchmarkRule": "Owner.kt"}}}
    source = tmp_path / "src"
    source.mkdir()
    (source / "Owner.kt").write_text("val rule = BenchmarkRule()\n")
    (source / "Note.kt").write_text("// BenchmarkRule is built elsewhere\n")
    assert owned_violations(layers, tmp_path) == set()
    (source / "Rogue.kt").write_text("val rule = BenchmarkRule()\n")
    assert owned_violations(layers, tmp_path) == {"owned: Rogue.kt names BenchmarkRule, only Owner.kt may"}
