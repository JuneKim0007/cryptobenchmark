import pytest

from perfrepair.dto.site import Scope, scope_id
from perfrepair.dto.unit import Unit, unit_id

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


def solo(scopes):
    return [Unit(unit_id(APP, [s.id]), (s.id,)) for s in scopes]


def run(tmp_path, *replacements, scopes=ALL, units=None):
    out = AppPaths(tmp_path, APP)
    doc = edit_app({s.id: s for s in scopes}, list(replacements), ROOT, out, load(), solo(scopes) if units is None else units)
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
    _, text = one(tmp_path, WRAP, pins(digest="SHA-256", mgf1="SHA-1"))
    assert text.splitlines()[WRAP.line].strip() == (
        'c.init(Cipher.ENCRYPT_MODE, key, javax.crypto.spec.OAEPParameterSpec("SHA-256", "MGF1", '
        'java.security.spec.MGF1ParameterSpec("SHA-1"), javax.crypto.spec.PSource.PSpecified.DEFAULT))')


# resolvedParameters of Cipher_RSA-ECB-OAEPWITHSHA-256ANDMGF1PADDING_ENCRYPT_SunJCE_k2048_i32_WARM_fixed, host JDK25 run
SUNJCE_OAEP256 = {"mode": "ECB", "padding": "OAEPWITHSHA-256ANDMGF1PADDING", "digest": "SHA-256", "mgf1": "SHA-1",
                  "labelBytes": 0, "keyBits": 2048}


def test_pin_parameters_takes_the_spec_fields_of_a_real_results_row(tmp_path):
    table = load()
    taken = {k: v for k, v in SUNJCE_OAEP256.items() if k in table.spec_for({"digest", "mgf1"}).pinnable}
    assert taken == {"digest": "SHA-256", "mgf1": "SHA-1"}
    row, text = one(tmp_path, WRAP, pins(**taken))
    assert row["status"] == "applied"
    assert 'OAEPParameterSpec("SHA-256", "MGF1", java.security.spec.MGF1ParameterSpec("SHA-1")' in text


def test_pin_parameters_finds_a_bare_init_in_an_apply_block(tmp_path):
    _, text = one(tmp_path, UNWRAP, pins(digest="SHA-256", mgf1="SHA-256"))
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


def _own_app(tmp_path, file, text, function, call):
    root = tmp_path / "app"
    (root / file).parent.mkdir(parents=True)
    (root / file).write_text(text)
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines, 1) if function in l)
    end = next(i for i in range(start, len(lines) + 1) if lines[i - 1] == "    }")
    line = next(i for i in range(start, end + 1) if "getInstance(" in lines[i - 1])
    s = Scope(scope_id(APP, file, function, line, call), APP, file, line, call, function, start, end,
              "Cipher", None, None, "default")
    doc = edit_app({s.id: s}, [replace(s, provider("Fast"))], root, AppPaths(tmp_path / "run", APP), load(), solo([s]))
    return doc["edits"][0]


@pytest.mark.parametrize("file, text", [
    # a nested Kotlin comment: the old edit lexer ended it at the first */ and saw an unbalanced {
    ("src/A.kt", 'object A {\n    fun f(): Cipher {\n        /* old /* inner */ { */\n'
                 '        return Cipher.getInstance("AES/GCM/NoPadding")\n    }\n}\n'),
    # Java has no string templates: the old edit lexer read "${" as one and swallowed the call
    ("src/A.java", 'class A {\n    Cipher f() throws Exception {\n        String t = "${";\n'
                   '        return Cipher.getInstance("AES/GCM/NoPadding");\n    }\n}\n'),
])
def test_edit_lexes_like_the_scope_step(tmp_path, file, text):
    row = _own_app(tmp_path, file, text, "f()", 'Cipher.getInstance("AES/GCM/NoPadding")')
    assert (row["status"], row["reason"]) == ("applied", None)
    assert '+        return Cipher.getInstance("AES/GCM/NoPadding", "Fast")' in row["diff"]


def together(*scopes):
    ids = [s.id for s in scopes]
    return [Unit(unit_id(APP, ids), tuple(ids))] + solo([s for s in ALL if s not in scopes])


def test_a_unit_applies_every_member(tmp_path):
    doc, out = run(tmp_path, replace(LITERAL, provider("Fast")), replace(ABSENT, provider("Fast")), units=together(LITERAL, ABSENT))
    assert {e["status"] for e in doc["edits"]} == {"applied"}
    text = (out.patched / LITERAL.file).read_text()
    assert call_line(text, LITERAL).endswith('"Fast");') and call_line(text, ABSENT).endswith('"Fast");')


def test_a_unit_with_a_member_that_stays_applies_the_replaced_one_alone(tmp_path):
    doc, out = run(tmp_path, replace(LITERAL, provider("Fast")), units=together(LITERAL, ABSENT))
    assert [(e["scope"], e["status"]) for e in doc["edits"]] == [(LITERAL.id, "applied")]
    text = (out.patched / LITERAL.file).read_text()
    assert call_line(text, LITERAL).endswith('"Fast");') and not call_line(text, ABSENT).endswith('"Fast");')


def test_one_rejected_member_rejects_its_unit_and_the_rows_say_why(tmp_path):
    doc, out = run(tmp_path, replace(LITERAL, provider("Fast")), replace(TEMPLATE), replace(ABSENT, provider("Fast")),
                   units=together(LITERAL, TEMPLATE))
    rows = {e["scope"]: e for e in doc["edits"]}
    assert rows[TEMPLATE.id]["status"] == "rejected" and "blockedBy" not in rows[TEMPLATE.id]
    assert rows[LITERAL.id] == {"scope": LITERAL.id, "status": "rejected", "reason": "unit_member_rejected", "diff": "",
                                "blockedBy": f"{TEMPLATE.id}: {rows[TEMPLATE.id]['reason']}"}
    assert rows[ABSENT.id]["status"] == "applied"
    text = (out.patched / LITERAL.file).read_text()
    assert 'getInstance("AES/GCM/NoPadding", "Slow")' in call_line(text, LITERAL) and call_line(text, ABSENT).endswith('"Fast");')


def test_two_members_with_overlapping_edits_reject_the_unit(tmp_path):
    same = scope(JAVA, "byte[] literal(byte[] in)", 'Cipher.getInstance("AES/GCM/NoPadding", "Slow")')
    twin = Scope(scope_id(APP, same.file, "other", same.line, same.call), APP, same.file, same.line, same.call, "other", same.start,
                 same.end, same.engineType, same.algorithm, same.provider, same.resolution)
    doc, _ = run(tmp_path, replace(same, provider("Fast")), replace(twin, provider("Faster")), scopes=[same, twin],
                 units=[Unit(unit_id(APP, [same.id, twin.id]), (same.id, twin.id))])
    assert {e["status"] for e in doc["edits"]} == {"rejected"}
    assert {e["reason"] for e in doc["edits"]} == {"overlapping_edits", "unit_member_rejected"}


def test_a_replacement_outside_every_unit_is_a_bug(tmp_path):
    with pytest.raises(ValueError, match="in no unit"):
        run(tmp_path, replace(LITERAL, provider("Fast")), units=[])


def test_the_validator_wants_blocked_by_exactly_with_its_reason():
    base = {"scope": LITERAL.id, "status": "rejected", "diff": ""}
    assert validate_edits({"schemaVersion": 1, "app": APP, "edits": [{**base, "reason": "unit_member_rejected"}]}, APP, {LITERAL.id})
    assert validate_edits({"schemaVersion": 1, "app": APP, "edits": [{**base, "reason": "no_change", "blockedBy": "x"}]}, APP, {LITERAL.id})
