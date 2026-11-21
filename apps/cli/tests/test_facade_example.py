"""The committed settings index template: it reads, and a copy beside it checks clean against the config/ layout it names."""
import shutil

import yaml

from cryptobench.shared import paths
from facade import check as check_module
from facade.check import check
from facade.index import read_index

APP_MANIFEST = '<manifest package="demo"><application /></manifest>'


def test_the_example_names_the_repository_defaults():
    repository = paths.repo()
    found = read_index(repository.facade_example)
    assert (found.results, found.crypto_config, found.llm_config) == (repository.default_results, repository.default_global, repository.perfrepair_settings)
    assert (found.harness_config, found.run_id, found.on_existing) == (None, None, "overwrite")


def test_a_copy_beside_the_example_checks_clean_in_a_config_layout(tmp_path, monkeypatch):
    repository, copy = paths.repo(), paths.repo(tmp_path)
    shutil.copytree(repository.benchmark_config, copy.benchmark_config)
    app = tmp_path / "app"
    (app / "src/main").mkdir(parents=True)
    (app / "build.gradle").write_text("apply plugin: 'com.android.application'\n")
    (app / "src/main/AndroidManifest.xml").write_text(APP_MANIFEST)
    settings = yaml.safe_load(repository.perfrepair_example.read_text())
    settings["apps"]["targets"] = [str(app)]
    copy.perf_repair_config.mkdir(parents=True)
    copy.perfrepair_settings.write_text(yaml.safe_dump(settings))
    index = copy.facade_example.parent / "settings.yaml"
    index.parent.mkdir(parents=True)
    shutil.copy(repository.facade_example, index)
    monkeypatch.setattr(check_module, "parse_all", lambda files: [
        {"global": str(f), "testSet": str(f.parent / yaml.safe_load(f.read_text())["selection"]["testSet"]), "bundled": []} for f in files])
    checked = check(index)
    assert checked.problems == []
    resolved = {n.key: n.path for n in checked.nodes if n.kind != "catalog"}
    assert (resolved["results"], resolved["crypto.config"], resolved["llm.config"]) == (copy.default_results, copy.default_global, copy.perfrepair_settings)
