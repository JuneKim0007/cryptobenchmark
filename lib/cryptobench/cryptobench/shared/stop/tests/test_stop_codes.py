"""cryptobench.shared.stop: the code table from the glossary, and halt_of on a fixed stop only."""
import pytest

from cryptobench.shared.errors.glossary import STOP
from cryptobench.shared.stop.codes import CODES, CODES_LIST
from cryptobench.shared.stop.terminate import halt_of


def test_each_code_is_in_the_table_once_with_a_next_step():
    assert len(CODES) == len(CODES_LIST) and all(c.next and c.action in c.allowed or c.fixed for c in CODES_LIST)


def test_halt_of_hands_back_a_fixed_stop_and_refuses_any_other_code():
    fixed = next(c for c in CODES_LIST if c.fixed and c.action == STOP)
    other = next(c for c in CODES_LIST if not c.fixed)
    halt = halt_of(fixed.code, "d", stage="s", step="t")
    assert halt.code == fixed.code and halt.next_step == fixed.next
    with pytest.raises(ValueError):
        halt_of(other.code, "d", stage="s", step="t")
