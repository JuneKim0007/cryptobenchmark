import pytest

from perfrepair.repair.edit import edit_app
from perfrepair.repair.edit.specs import load
from perfrepair.run_dir import AppPaths
from perfrepair.validation.repair import validate_edits
from repair_fixture import APP, JAVA, KOTLIN, ROOT, algorithm, digests, pins, provider, replace, scope

LITERAL = scope(JAVA, "byte[] literal(byte[] in)", 'Cipher.getInstance("AES/GCM/NoPadding", "Slow")')
ABSENT = scope(JAVA, "byte[] absent(byte[] in)", 'Cipher.getInstance("AES/GCM/NoPadding")')
LOOKED_UP = scope(JAVA, "byte[] lookedUp(byte[] in)", 'Cipher.getInstance(ALG, Security.getProvider("Slow"))')
MULTI = scope(JAVA, "byte[] multiLine(byte[] in, byte[] iv)", 'Cipher.getInstance("AES/GCM/NoPadding", "Slow")')
NESTED = scope(JAVA, "byte[] nested(byte[] in)", 'Cipher.getInstance(name(prefix("AES"), "GCM"), "Slow")')
TWICE = scope(JAVA, "byte[] twice(byte[] in)", 'Cipher.getInstance("AES/GCM/NoPadding")')
WRAP = scope(KOTLIN, "fun wrap(", 'Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding")')
UNWRAP = scope(KOTLIN, "fun unwrap(", 'Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding", "Slow")')
TEMPLATE = scope(KOTLIN, "fun template(", 'Cipher.getInstance("AES/$mode/NoPadding", "Slow")')
ALL = [LITERAL, ABSENT, LOOKED_UP, MULTI, NESTED, TWICE, WRAP, UNWRAP, TEMPLATE]


def run(tmp_path, *replacements, scopes=ALL):
    out = AppPaths(tmp_path, APP)
    doc = edit_app({s.id: s for s in scopes}, list(replacements), ROOT, out, load())
    assert validate_edits(doc, APP, {s.id for s in scopes}) == []
    return doc, out


def one(tmp_path, s, *edits):
    doc, out = run(tmp_path, replace(s, *edits))
    [row] = doc["edits"]
    patched = out.patched / s.file
    return row, patched.read_text() if patched.exists() else None


def call_line(text, s):
    return text.splitlines()[s.line - 1].strip()


def test_set_provider_rewrites_a_literal_provider(tmp_path):
    row, text = one(tmp_path, LITERAL, provider("Fast"))
    assert row["status"] == "applied" and row["reason"] is None
    assert call_line(text, LITERAL) == 'Cipher c = Cipher.getInstance("AES/GCM/NoPadding", "Fast");'
    assert '+        Cipher c = Cipher.getInstance("AES/GCM/NoPadding", "Fast");' in row["diff"]


def test_set_provider_appends_an_absent_provider(tmp_path):
    _, text = one(tmp_path, ABSENT, provider("Fast"))
    assert call_line(text, ABSENT) == 'Cipher c = Cipher.getInstance("AES/GCM/NoPadding", "Fast");'


def test_set_provider_rewrites_the_name_inside_get_provider(tmp_path):
    _, text = one(tmp_path, LOOKED_UP, provider("Fast"))
    assert call_line(text, LOOKED_UP) == 'Cipher c = Cipher.getInstance(ALG, Security.getProvider("Fast"));'


def test_set_provider_spans_a_multi_line_call_with_a_comment_and_keeps_line_numbers(tmp_path):
    _, text = one(tmp_path, MULTI, provider("Fast"))
    original = (ROOT / JAVA).read_text()
    assert text.count("\n") == original.count("\n")
    assert text.splitlines()[MULTI.line + 1].strip() == '"Fast");'
    assert "// the app's choice" in text.splitlines()[MULTI.line]


def test_set_provider_finds_the_closing_paren_past_nested_calls(tmp_path):
    _, text = one(tmp_path, NESTED, provider("Fast"))
    assert call_line(text, NESTED) == 'Cipher c = Cipher.getInstance(name(prefix("AES"), "GCM"), "Fast");'


def test_set_provider_in_kotlin_escapes_a_dollar(tmp_path):
    _, text = one(tmp_path, UNWRAP, provider("Fa$t"))
    assert 'Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding", "Fa\\$t").apply {' in text


def test_set_algorithm_rewrites_a_literal_in_a_multi_line_kotlin_call(tmp_path):
    row, text = one(tmp_path, TEMPLATE, algorithm("AES/GCM/NoPadding"))
    assert row["status"] == "applied"
    assert text.splitlines()[TEMPLATE.line].strip() == '"AES/GCM/NoPadding",'


def test_set_algorithm_with_provider_on_one_call(tmp_path):
    _, text = one(tmp_path, LITERAL, algorithm("AES/CBC/PKCS5Padding"), provider("Fast"))
    assert call_line(text, LITERAL) == 'Cipher c = Cipher.getInstance("AES/CBC/PKCS5Padding", "Fast");'


def test_set_algorithm_never_edits_a_constant(tmp_path):
    row, text = one(tmp_path, LOOKED_UP, algorithm("AES/CBC/PKCS5Padding"))
    assert (row["status"], row["reason"], row["diff"], text) == ("rejected", "algorithm_not_literal", "", None)


def test_pin_parameters_appends_a_rendered_spec_to_the_kotlin_init(tmp_path):
    _, text = one(tmp_path, WRAP, pins(digest="SHA-256", mgfDigest="SHA-1"))
    assert text.splitlines()[WRAP.line].strip() == (
        'c.init(Cipher.ENCRYPT_MODE, key, javax.crypto.spec.OAEPParameterSpec("SHA-256", "MGF1", '
        'java.security.spec.MGF1ParameterSpec("SHA-1"), javax.crypto.spec.PSource.PSpecified.DEFAULT))')


def test_pin_parameters_finds_a_bare_init_in_an_apply_block(tmp_path):
    _, text = one(tmp_path, UNWRAP, pins(digest="SHA-256", mgfDigest="SHA-256"))
    assert text.splitlines()[UNWRAP.line].strip().startswith(
        'init(Cipher.DECRYPT_MODE, key, javax.crypto.spec.OAEPParameterSpec("SHA-256"')


def test_pin_parameters_overrides_only_pinned_fields_of_an_existing_spec(tmp_path):
    _, text = one(tmp_path, MULTI, pins(tagBits=128))
    assert "c.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, iv));" in text


def test_pin_parameters_renders_a_fresh_iv_only_when_encrypting(tmp_path):
    _, text = one(tmp_path, ABSENT, pins(tagBits=128, ivBytes=12))
    assert "new javax.crypto.spec.GCMParameterSpec(128, ((java.util.function.Supplier<byte[]>)" in text
    row, _ = one(tmp_path / "decrypt", MULTI, pins(tagBits=128, ivBytes=12))
    assert row["reason"] == "unsupported_expression"


@pytest.mark.parametrize("s, edit, reason", [
    (TWICE, pins(tagBits=128), "ambiguous_init"),
    (WRAP, pins(colour="red"), "unknown_parameters"),
    (WRAP, pins(), "missing_parameter"),
    (LITERAL, provider("Slow"), "no_change"),
    (LITERAL, provider(None), "missing_parameter"),
])
def test_an_edit_that_cannot_apply_exactly_is_rejected_with_its_reason(tmp_path, s, edit, reason):
    row, text = one(tmp_path, s, edit)
    assert (row["status"], row["reason"], text) == ("rejected", reason, None)


def test_a_call_that_moved_or_changed_is_rejected(tmp_path):
    moved = scope(JAVA, "byte[] literal(byte[] in)", LITERAL.call, line_shift=1)
    changed = scope(JAVA, "byte[] literal(byte[] in)", 'Cipher.getInstance("AES/GCM/NoPadding", "Other")')
    for s in (moved, changed):
        doc, _ = run(tmp_path, replace(s, provider("Fast")), scopes=[s])
        assert doc["edits"][0]["reason"] == "call_moved"


def test_rejected_scopes_leave_no_copy_and_applied_ones_share_their_file(tmp_path):
    doc, out = run(tmp_path, replace(LITERAL, provider("Fast")), replace(ABSENT, provider("Fast")),
                   replace(TWICE, pins(tagBits=128)))
    assert [e["status"] for e in doc["edits"]] == [
        {LITERAL.id: "applied", ABSENT.id: "applied", TWICE.id: "rejected"}[e["scope"]] for e in doc["edits"]]
    text = (out.patched / JAVA).read_text()
    assert text.count('"Fast"') == 2
    assert (out.original / JAVA).read_bytes() == (ROOT / JAVA).read_bytes()
    assert not (out.patched / KOTLIN).exists()


def test_keep_decisions_are_not_listed(tmp_path):
    keep = replace(LITERAL, provider("Fast"))
    doc, _ = run(tmp_path, type(keep)(keep.scope, "keep", None, (), (), "slower"))
    assert doc["edits"] == []


def test_editing_is_deterministic_and_never_touches_the_app(tmp_path):
    before = digests()
    replacements = [replace(s, provider("Fast")) for s in ALL]
    first, out = run(tmp_path / "a", *replacements)
    second, again = run(tmp_path / "b", *reversed(replacements))
    assert first == second
    assert digests(out.patched) == digests(again.patched)
    assert digests() == before


def test_a_replacement_for_an_unknown_scope_is_an_input_error(tmp_path):
    with pytest.raises(ValueError, match="missing from scopes.json"):
        run(tmp_path, replace(LITERAL, provider("Fast")), scopes=[ABSENT])
