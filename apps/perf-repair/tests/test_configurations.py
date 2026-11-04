from dataclasses import replace

import pytest

from helpers import row, summary

from perfrepair.dto.dossier import TOO_FEW_RUNS
from perfrepair.dto.measurement import ESTIMATED
from perfrepair.result.configurations import config_of, estimates, parse_label


@pytest.mark.parametrize("kind", [None, ESTIMATED])
@pytest.mark.parametrize("key_size, input_size", [(128, 1024), (None, None)])
def test_a_stored_configuration_parses_back_to_its_fields(kind, key_size, input_size):
    mine, theirs = row("r1", "P1", key_size=key_size, input_size=input_size), row("r2", "P2", key_size=key_size, input_size=input_size)
    c = config_of(mine)
    m = {"r1": {"energyJ": replace(summary(10.0), kind=kind)}, "r2": {"energyJ": replace(summary(5.0), kind=kind)}}
    (found,), () = estimates([c], {c: mine}, {c: theirs}, m, ("energyJ",))
    parsed = parse_label(found.configuration)
    assert (parsed["op"], parsed["key"], parsed["input"], parsed["phase"]) == tuple(map(str, c))
    assert bool(parsed["estimated"]) == (kind == ESTIMATED)


def test_text_of_another_shape_does_not_parse():
    assert parse_label("OP1 at 1024") is None


def test_a_side_with_too_few_runs_gives_no_estimate_and_says_why():
    mine, theirs = row("r1", "P1", key_size=128, input_size=1024), row("r2", "P2", key_size=128, input_size=1024)
    c = config_of(mine)
    one_run = replace(summary(5.0), n=1, processes=((5.0,),))
    found, absent = estimates([c], {c: mine}, {c: theirs}, {"r1": {"timeNs": summary(10.0)}, "r2": {"timeNs": one_run}}, ("timeNs",))
    assert found == () and [n.reason for n in absent] == [TOO_FEW_RUNS]
