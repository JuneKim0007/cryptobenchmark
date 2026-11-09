import pytest

from cryptobench.paths import AppTree

def test_app_paths_refuse_a_name_that_is_not_one_segment(tmp_path):
    with pytest.raises(ValueError, match="app name"):
        AppTree(tmp_path, "../elsewhere")
