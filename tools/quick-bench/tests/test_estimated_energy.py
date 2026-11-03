"""A run whose energy is estimated says so in summary.md, on its count chart's label and on the console."""
import json, pathlib, shutil, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import analyze, chart_model  # noqa: E402

TESTS = pathlib.Path(__file__).parent


def with_energy(tmp_path, block):
    document = json.loads((TESTS / "fixture_benchmark.json").read_text())
    document["cases"][0]["metrics"]["energyJ"] = block
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps(document))
    return path


def test_an_estimated_run_is_marked(tmp_path):
    path = with_energy(tmp_path, {"iterations": 9, "runs": [0.5], "source": "manafa", "kind": "estimated"})
    analyze.build(path, tmp_path)
    assert (tmp_path / "summary.md").read_text().endswith("\nenergyJ is estimated by manafa, not measured.\n")
    case = json.loads(path.read_text())["cases"][0]
    assert chart_model.summarize_count(case, {}, "energyJ")["label"].endswith("(estimated)")


def test_a_measured_run_writes_the_table_it_always_wrote(tmp_path):
    analyze.build(with_energy(tmp_path, {"iterations": 9, "runs": [0.5], "source": "rails", "kind": "measured"}), tmp_path)
    rails = (tmp_path / "summary.md").read_text()
    plain = tmp_path / "plain"
    plain.mkdir()
    shutil.copy(TESTS / "fixture_benchmark.json", plain / "benchmark.json")
    analyze.build(plain / "benchmark.json", plain)
    assert "estimated" not in rails and rails == (plain / "summary.md").read_text()
