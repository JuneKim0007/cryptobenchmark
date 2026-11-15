import yaml

from cryptobench.stages.verification import known_answers


def test_user_folder_is_relative_to_the_global_file(tmp_path):
    settings = tmp_path / "g.yaml"
    settings.write_text(yaml.safe_dump({"selection": {"testSet": "t", "knownVectors": "mine"}}))
    assert known_answers.user_vectors(settings) == tmp_path / "mine"
