"""tools/seed_groups.py proposes what the catalog's reader accepts, and leaves to the model a name whose signature stays open."""
import importlib.util
import pathlib
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools" / "seed_groups.py"


@pytest.fixture(scope="module")
def tool():
    spec = importlib.util.spec_from_file_location("seed_groups", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_proposal_is_what_the_reader_accepts_and_leaves_open_names_out(tool, tmp_path):
    from perfrepair.catalog.groups import load
    document, left = tool.propose()
    path = tmp_path / "groups.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False))
    catalog = load(path)
    listed = {(g.family, name) for g in catalog.groups for _, name in g.members}
    assert listed and ("cipher.pair", "RSA/ECB/OAEPPadding") not in listed and "cipher.pair RSA/ECB/OAEPPadding" in left


def test_the_committed_catalog_lists_nothing_a_proposal_leaves_open(tool):
    committed = yaml.safe_load((ROOT / "apps/perf-repair/src/perfrepair/catalog/groups.yaml").read_text())
    names = {f"{f} {m['name']}" for f, rows in committed["families"].items() for r in rows for m in r["members"]}
    assert not names & set(tool.propose()[1]), sys.path
