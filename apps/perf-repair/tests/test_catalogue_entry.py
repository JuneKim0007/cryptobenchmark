"""Static entry checks: form, family against engine type, one id across the catalogues, one group."""
import copy

from perfrepair.catalog.algorithms import Algorithms, Entry, algorithms
from perfrepair.catalog.families import Families
from perfrepair.catalog.groups import group_catalog
from perfrepair.validation.catalogue_entry import catalogue_check, entry_check

FAMILIES = Families.load()
SHA = "MessageDigest|SHA-256"


def _with(entry: Entry) -> Algorithms:
    catalogue = algorithms()
    return Algorithms((*catalogue.entries, entry), catalogue.common)


def _sha(family="digest.none", identifier=SHA, change=None) -> Entry:
    raw = copy.deepcopy(algorithms().of("digest.none", SHA).raw)
    if change:
        change(raw)
    return Entry(identifier, family, raw)


def test_the_packaged_catalogues_hold_only_today_s_known_gaps():
    # SLH-DSA and XWING have facts but no name yet
    assert catalogue_check(algorithms(), group_catalog(), FAMILIES) == [
        "signature.pair Signature|SLH-DSA-SHA2-128S: id is in 0 groups, not one",
        "keypairgen.none KeyPairGenerator|SLH-DSA-SHA2-128S: id is in 0 groups, not one",
        "keypairgen.none KeyPairGenerator|XWING: id is in 0 groups, not one"]


def test_a_listed_entry_passes():
    entry = algorithms().of("digest.none", SHA)
    assert entry_check(entry, algorithms(), group_catalog(), FAMILIES) == []


def test_a_new_entry_already_held_is_refused():
    entry = _sha()
    assert "id is in 2 catalogues: ['digest.none', 'digest.none']" in entry_check(entry, _with(entry), group_catalog(), FAMILIES)


def test_a_new_entry_in_no_group_is_refused():
    entry = _sha(identifier="MessageDigest|SHA-999")
    assert entry_check(entry, _with(entry), group_catalog(), FAMILIES) == ["id is in 0 groups, not one"]


def test_a_family_that_does_not_fit_the_engine_type_is_refused():
    entry = _sha(family="mac.secret", identifier="MessageDigest|SHA-998")
    assert "engine type MessageDigest does not fit family mac.secret (Mac)" in entry_check(entry, _with(entry), group_catalog(),
                                                                                           FAMILIES)


def test_a_malformed_entry_names_its_form_problem():
    entry = _sha(identifier="MessageDigest|SHA-997", change=lambda r: r.pop("provenance"))
    assert entry_check(entry, _with(entry), group_catalog(), FAMILIES)[0].startswith("fields missing ['provenance']")
