import pytest
import yaml
from site_replace_data import APP, doc, dossier

from perfrepair.dto.site import Option
from perfrepair.files import write_json
from perfrepair.repair.__main__ import main
from perfrepair.repair.test_set import build_test_set
from perfrepair.run_dir import AppPaths

ALG = "ALG-A/MODE-X"


def test_the_test_set_holds_each_current_item_and_every_option_once():
    a = dossier(options=(Option("R1", f"TypeA|{ALG}|P2", {}), Option("R2", "TypeA|ALG-B|P1", {})))
    b = dossier(file="src/Other.kt", options=(Option("R1", f"TypeA|{ALG}|P2", {}),))
    assert build_test_set(doc(a, b), APP) == {
        "schemaVersion": 1, "description": f"call sites of {APP} and their replacements",
        "include": [{"provider": "P1", "type": "TypeA", "name": ALG},
                    {"provider": "P2", "type": "TypeA", "name": ALG},
                    {"provider": "P1", "type": "TypeA", "name": "ALG-B"}]}


def test_a_test_set_refuses_another_app_or_nothing_to_measure():
    with pytest.raises(ValueError, match=f"not '{APP}'"):
        build_test_set(doc(dossier(), app="other"), APP)
    with pytest.raises(ValueError, match="nothing to measure"):
        build_test_set(doc(), APP)


def test_the_test_set_command_reads_the_app_dossiers(tmp_path):
    paths = AppPaths(tmp_path, APP)
    paths.root.mkdir(parents=True)
    write_json(paths.dossiers, doc(dossier(options=(Option("R1", f"TypeA|{ALG}|P2", {}),))))
    out = tmp_path / "set.yaml"
    assert main(["test-set", "--run", str(tmp_path), "--app", APP, "-o", str(out)]) == 0
    assert [i["provider"] for i in yaml.safe_load(out.read_text())["include"]] == ["P1", "P2"]


def test_app_paths_refuse_a_name_that_is_not_one_segment(tmp_path):
    with pytest.raises(ValueError, match="app name"):
        AppPaths(tmp_path, "../elsewhere")
