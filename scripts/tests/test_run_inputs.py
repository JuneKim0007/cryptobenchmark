import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import run_inputs  # noqa: E402

BASE = "schemaVersion: 1\nselection: {testSet: sets/a.yaml}\nrun: {seed: 1, phases: [WARM]}\nproviders: {bundled: [{artifact: 'g:a:1', create: X}]}\n"


def digests(tmp_path, text=BASE, test_set="include: []\n"):
    (tmp_path / "sets").mkdir(exist_ok=True)
    (tmp_path / "sets" / "a.yaml").write_text(test_set)
    (tmp_path / "global.yaml").write_text(text)
    return run_inputs.digests(tmp_path / "global.yaml")


def test_a_comment_or_key_order_changes_nothing(tmp_path):
    first = digests(tmp_path)
    reordered = "# note\nrun: {phases: [WARM], seed: 1}\nschemaVersion: 1\nselection: {testSet: sets/a.yaml}\n" \
                "providers: {bundled: [{create: X, artifact: 'g:a:1'}]}\n"
    assert digests(tmp_path, reordered) == first


def test_the_bundled_list_is_its_own_input(tmp_path):
    first = digests(tmp_path)
    added = digests(tmp_path, BASE.replace("create: X}]", "create: X}, {artifact: 'g:b:2', create: Y}]"))
    assert added["bundled"] != first["bundled"] and added["config"] == first["config"]


def test_the_config_covers_its_test_set(tmp_path):
    first = digests(tmp_path)
    assert digests(tmp_path, BASE.replace("seed: 1", "seed: 2"))["config"] != first["config"]
    changed = digests(tmp_path, test_set="include: [{type: Mac}]\n")
    assert changed["config"] != first["config"] and changed["bundled"] == first["bundled"]


def test_analysis_shows_results_and_reruns_nothing(tmp_path):
    first = digests(tmp_path)
    assert digests(tmp_path, BASE + "analysis: {units: {latency: us}, charts: []}\n") == first
