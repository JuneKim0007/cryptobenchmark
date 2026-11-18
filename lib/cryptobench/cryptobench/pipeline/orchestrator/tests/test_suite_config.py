import yaml

from cryptobench.pipeline.orchestrator import suite_config


def test_a_suite_config_is_a_composition_of_the_config_and_its_overlays(tmp_path):
    written = suite_config.written(tmp_path / "base.yaml", (tmp_path / "energy.yaml",), tmp_path / "tier1.yaml", tmp_path / "s/t/tier1.global.yaml")
    assert yaml.safe_load(written.read_text()) == {"schemaVersion": 1, "layers": [str(tmp_path / "base.yaml"), str(tmp_path / "energy.yaml")],
                                                   "selection": {"testSet": str(tmp_path / "tier1.yaml")}}
