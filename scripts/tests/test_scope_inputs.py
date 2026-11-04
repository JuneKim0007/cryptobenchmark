"""Input synthesis: primitives by value, key pairs through ScopeKeys, a file of seeded bytes; each a generated line the wrapper compiles."""
import pathlib, sys
from types import SimpleNamespace

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from scope import generate as scope_generate  # noqa: E402
from scope import inputs as scope_inputs  # noqa: E402

SCOPE = SimpleNamespace(key_size=2048, input_size=64, input_source="run", current="Cipher|RSA/ECB/OAEPPadding|A", option="Cipher|RSA/ECB/OAEPPadding|BC")


def expression(type_text, scope=SCOPE):
    return scope_inputs.expression(SimpleNamespace(name="p", type=type_text), scope)


@pytest.mark.parametrize("java,kotlin,value", [("boolean", "Boolean", "true"), ("byte", "Byte", "(1).toByte()"), ("short", "Short", "(1).toShort()"),
                                               ("int", "Int", "1"), ("long", "Long", "1L"), ("float", "Float", "1f"),
                                               ("double", "Double", "1.0"), ("char", "Char", "'a'")])
def test_each_primitive_has_one_value_under_both_spellings_and_needs_no_size(java, kotlin, value):
    empty = SimpleNamespace(key_size=None, input_size=None, input_source="run", current=None, option=None)
    assert expression(java, empty) == value and expression(f"{kotlin}?", empty) == value


def test_key_pair_parameters_come_from_one_pair_at_the_options_item_and_size():
    made = 'ScopeKeys.pair("Cipher", "RSA/ECB/OAEPPadding", "BC", 2048, "BC")'
    assert expression("java.security.KeyPair") == made
    assert expression("PrivateKey") == made + ".private" and expression("PublicKey") == made + ".public"


def test_each_side_decodes_the_one_generated_pair_through_its_own_provider():
    before = scope_inputs.expression(SimpleNamespace(name="p", type="PrivateKey"), SCOPE, "before")
    assert before == 'ScopeKeys.pair("Cipher", "RSA/ECB/OAEPPadding", "BC", 2048, "A").private'


def test_a_key_pair_without_a_size_and_a_file_without_a_size_say_which_input_is_missing():
    empty = SimpleNamespace(key_size=None, input_size=None, input_source="app", current=None, option="Cipher|RSA|BC")
    with pytest.raises(scope_inputs.InputError, match="missing_input: keySize for p, none from app"):
        expression("PrivateKey", empty)
    with pytest.raises(scope_inputs.InputError, match="missing_input: inputSize for p, none from app"):
        expression("java.io.File", empty)


def test_a_file_is_seeded_bytes_at_the_input_size():
    assert expression("File") == "ScopeInputs.file(64, 7)"


def test_a_function_of_every_new_kind_is_generated_and_a_failing_input_stays_in_its_own_scope(tmp_path):
    source = tmp_path / "before.java"
    source.write_text("int all(boolean a, byte b, short c, int d, long e, float f, double g, char h, File i, PrivateKey j, PublicKey k, KeyPair l) { return d; }\n")
    harness = tmp_path / "harness.yaml"
    harness.write_text(yaml.safe_dump({"schemaVersion": 5, "app": "a", "scopes": [{
        "id": "aaaaaaaaaaaa", "language": "java", "function": "all", "before": "before.java", "after": "before.java",
        "imports": ["import java.io.File;", "import java.security.PrivateKey;", "import java.security.PublicKey;", "import java.security.KeyPair;"],
        "inputs": {"inputSize": 64, "keySize": 2048, "from": "run"}, "current": "Cipher|RSA|A", "option": "Cipher|RSA|B",
        "metrics": ["timeNs"], "dependencies": [], "callSite": {"operation": "DECRYPT", "variant": "notFixed"}}]}))
    plan, compiled = scope_generate.generate(harness, tmp_path / "root", tmp_path / "out", compiler=lambda root: [])
    assert compiled == ["aaaaaaaaaaaa"], plan.read_text()
    catalog = (tmp_path / "root" / scope_generate.scope_wrapper.FOLDER / "GeneratedScopes.kt").read_text()
    assert 'ScopeCatalog.guarded("aaaaaaaaaaaa") { saaaaaaaaaaaa() }' in catalog
    assert 'ScopeKeys.pair("Cipher", "RSA", "B", 2048, "A").private' in catalog
    assert "ScopeInputs.file(64, 7)" in catalog and 'ScopeKeys.pair("Cipher", "RSA", "B", 2048, "B").private' in catalog
