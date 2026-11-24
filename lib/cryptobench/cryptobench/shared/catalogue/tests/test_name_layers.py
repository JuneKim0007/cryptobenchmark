import pytest
import yaml

from cryptobench.shared import paths
from cryptobench.shared.catalogue.name_layers import ServiceSpellings, merged
from cryptobench.shared.catalogue.names import Canonical, Names, NamesError

CASES = yaml.safe_load((paths.repo().contract_catalogue / "name-layers-cases.yaml").read_text())


ROWS = [ServiceSpellings(r["provider"], r["type"], r["algorithm"], tuple(r["aliases"])) for r in CASES["capture"]]


@pytest.fixture(scope="module")
def layered():
    return merged(Names.load(), ROWS)


@pytest.mark.parametrize("rows", [ROWS, ROWS[::-1]], ids=["capture order", "reversed"])
def test_the_shared_conflicts_are_the_merged_ones_in_any_row_order(rows):
    assert merged(Names.load(), rows).conflicts == {(c["type"], c["alias"]): c["why"] for c in CASES["conflicts"]}


@pytest.mark.parametrize("case", CASES["lookups"], ids=lambda c: f"{c['type']}:{c['name']}")
def test_the_shared_lookups_resolve(layered, case):
    if "refused" in case:
        with pytest.raises(NamesError) as refused:
            layered.canonical(case["type"], case["name"])
        assert str(refused.value) == case["refused"]
    else:
        want = case["canonical"]
        assert layered.canonical(case["type"], case["name"]) == Canonical(want["name"], want["keySize"], want["known"])
    assert layered.key_or_spelling(case["type"], case["name"]) == tuple(case["key"])


def test_no_capture_is_the_base():
    base = Names.load()
    assert merged(base) == base and merged(base, []) == base
