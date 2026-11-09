"""Static entry checks: form, family against engine type, one id across the catalogues, one group."""
import copy

from cryptobench.catalogue.algorithms import Algorithms, Entry, algorithms, entry_problems
from cryptobench.catalogue.families import Families
from cryptobench.catalogue.groups import group_catalog
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


def test_the_packaged_catalogues_pass_every_static_check():
    assert catalogue_check(algorithms(), group_catalog(), FAMILIES) == []


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


def _problems(family, identifier, change):
    entry = algorithms().of(family, identifier)
    raw = copy.deepcopy(entry.raw)
    change(raw)
    return entry_problems(Entry(entry.id, entry.family, raw), algorithms().common)


def test_a_generator_or_an_agreement_states_no_result_length():
    assert any("states no result length" in p for p in _problems("keygen.none", "KeyGenerator|AES", lambda r: r["conditions"]["output"].update(bytes=8)))
    assert any("states no result length" in p for p in _problems("agreement.peer", "KeyAgreement|ECDH", lambda r: r["conditions"]["output"].update(bytes=8)))


def test_a_stated_length_is_what_the_formula_fixes():
    assert any("is not what formula" in p for p in _problems("signature.pair", "Signature|SHA256withECDSA", lambda r: r["conditions"]["output"].update(bytes=8)))


def test_a_row_goes_only_to_a_call_its_role_takes():
    def move(raw):
        next(r for r in raw["required"] if r["name"] == "secretKey").update(passedTo="update")
    assert any("passedTo 'update' on Cipher" in p for p in _problems("cipher.secret", "Cipher|AES/CBC/NoPadding", move))
