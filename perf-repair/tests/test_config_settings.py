from pathlib import Path

import pytest
import yaml

from perfrepair.config.settings import Agent, ConfigError, Settings, parse

EXAMPLE = Path(__file__).parents[1] / "perfrepair.example.yaml"


def test_the_example_file_parses_and_names_every_section(tmp_path):
    document = yaml.safe_load(EXAMPLE.read_text())
    assert set(document) == {"agent", "paths", "grouping", "guide", "ai", "screening"}
    assert isinstance(parse(document, tmp_path), Settings)


def test_values_parse_into_sections_with_paths_relative_to_the_file(tmp_path):
    s = parse({"agent": {"backend": "dry-run", "claudeBinary": "/opt/claude"},
               "paths": {"run": "runs/a", "prompts": "/abs/prompts"},
               "grouping": {"turns": 4, "supervisor": {"effort": "low"}},
               "guide": {"device": True, "agent": {"model": "m"}},
               "screening": {"catalog": "cat.yaml", "unknown": "unverified"}}, tmp_path)
    assert s.agent == Agent(backend="dry-run", claudeBinary="/opt/claude")
    assert s.paths.run == tmp_path / "runs/a" and s.paths.prompts == Path("/abs/prompts")
    assert s.grouping.turns == 4 and s.grouping.supervisor.effort == "low" and s.guide.agent.model == "m"
    assert s.screening.catalog == tmp_path / "cat.yaml" and s.get("guide.device") is True


def test_empty_file_and_null_values_are_unset(tmp_path):
    assert parse(None, tmp_path) == Settings() == parse({"agent": None, "grouping": {"limit": None}}, tmp_path)


@pytest.mark.parametrize("document, message", [
    ({"agnt": {}}, "unknown_keys: <root> ['agnt'], known ['agent', 'paths', 'grouping', 'guide', 'ai', 'screening']"),
    ({"grouping": {"assign": {"efort": "low"}}},
     "unknown_keys: grouping.assign ['efort'], known ['backend', 'model', 'effort', 'claudeBinary']"),
    ({"agent": {"effort": "hgh"}}, "invalid: agent.effort hgh, one of ['low', 'medium', 'high', 'xhigh', 'max']"),
    ({"ai": {"replace": {"backend": "openai"}}}, "invalid: ai.replace.backend openai, one of ['claude', 'claude-code', 'dry-run']"),
    ({"screening": {"unknown": "guess"}}, "invalid: screening.unknown guess, one of ['model', 'unverified']"),
    ({"grouping": {"turns": 0}}, "invalid: grouping.turns 0, a positive integer"),
    ({"guide": {"device": "yes"}}, "invalid: guide.device yes, true or false"),
    ({"paths": {"run": 3}}, "invalid: paths.run 3, a path"),
    ({"agent": "claude"}, "invalid: agent claude, a mapping"),
])
def test_unknown_keys_and_invalid_values_are_refused_with_their_path(tmp_path, document, message):
    with pytest.raises(ConfigError) as e:
        parse(document, tmp_path)
    assert str(e.value) == message


@pytest.mark.parametrize("document", [
    {"agent": {"apiKey": "x"}}, {"ANTHROPIC_API_KEY": "x"}, {"guide": {"agent": {"auth_token": "x"}}},
    {"agent": {"model": "sk-ant-abc"}},
])
def test_anything_that_looks_like_a_secret_is_refused(tmp_path, document):
    with pytest.raises(ConfigError, match="^secret_key: .*keep secrets in the environment or .env"):
        parse(document, tmp_path)
