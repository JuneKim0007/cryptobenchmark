"""The parse-only check through the real CheckConfigKt."""
import pytest

from cryptobench.stages.configuration import config_check


def test_the_real_parser_catches_a_typo_and_a_bad_provider_before_any_build(tmp_path):
    good = tmp_path / "global.yaml"
    (tmp_path / "set.yaml").write_text("schemaVersion: 1\n")
    good.write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\nproviders: {bundled: [{artifact: 'a:b:1', create: org.example.C}]}\n")
    [one] = config_check.parse_all([good])
    assert one["testSet"].endswith("set.yaml") and one["bundled"] == [{"artifact": "a:b:1", "create": "org.example.C"}]
    good.write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\nrnu: {seed: 1}\n")
    with pytest.raises(config_check.ConfigCheckError, match="unknown_section"):
        config_check.parse_all([good])
    good.write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\nproviders: {bundled: [{artifact: 'a:b:1', create: C}]}\n")
    with pytest.raises(config_check.ConfigCheckError, match="invalid_create"):
        config_check.parse_all([good])
