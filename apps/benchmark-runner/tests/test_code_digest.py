import sys

import pytest

from scope import code_digest


def tree(root):
    (root / "a").mkdir(parents=True)
    (root / "a" / "one.py").write_text("1")
    (root / "two.py").write_text("2")
    return ("a/*.py", "two.py")


def test_every_pattern_of_the_repository_matches():
    assert len(code_digest.digest()) == 64


def test_a_changed_file_changes_the_digest_and_the_location_does_not(tmp_path):
    patterns = tree(tmp_path / "x")
    tree(tmp_path / "y")
    first = code_digest.digest(tmp_path / "x", patterns)
    assert code_digest.digest(tmp_path / "y", patterns) == first
    (tmp_path / "x" / "two.py").write_text("changed")
    assert code_digest.digest(tmp_path / "x", patterns) != first


def test_a_pattern_that_matches_nothing_is_one_coded_error(tmp_path):
    patterns = tree(tmp_path)
    with pytest.raises(code_digest.CodeDigestError, match=r"^missing_file: moved/\*\.py matches nothing under "):
        code_digest.digest(tmp_path, (*patterns, "moved/*.py"))


def test_the_run_reports_it_as_its_own_line():
    import pipeline
    error = code_digest.CodeDigestError("missing_file: moved/*.py matches nothing")
    assert pipeline.failure_line(error) == "missing_file: moved/*.py matches nothing"
