import pytest

from perfrepair.run_dir import AppPaths

def test_app_paths_refuse_a_name_that_is_not_one_segment(tmp_path):
    with pytest.raises(ValueError, match="app name"):
        AppPaths(tmp_path, "../elsewhere")
