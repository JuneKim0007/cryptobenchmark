"""Which parameter types a scope wrapper can synthesise, and the ScopeInputs call that builds each."""
import re

SEED = 7
# kind per normalised type; every other type is unsupported_parameter.
KINDS = {"byte[]": "bytes", "ByteArray": "bytes", "String": "text", "CharSequence": "text",
         "char[]": "chars", "CharArray": "chars", "SecretKey": "key", "Key": "key", "SecretKeySpec": "key", "File": "file",
         "PrivateKey": "private", "PublicKey": "public", "KeyPair": "pair"}
# One fixed value per primitive, Java and Kotlin spellings: the wrapper's source is Kotlin; a non-zero value walks past an empty loop.
PRIMITIVES = {"true": ("boolean", "Boolean"), "(1).toByte()": ("byte", "Byte"), "(1).toShort()": ("short", "Short"),
              "1": ("int", "Int", "Integer"), "1L": ("long", "Long"), "1f": ("float", "Float"), "1.0": ("double", "Double"),
              "'a'": ("char", "Char", "Character")}
LITERALS = {name: literal for literal, names in PRIMITIVES.items() for name in names}
PAIR_MEMBERS = {"private": ".private", "public": ".public", "pair": ""}
KOTLIN_TYPES = {"bytes": "ByteArray", "text": "String", "chars": "CharArray"}


class InputError(Exception):
    """The message is the not_compilable reason."""


def normalised(type_text):
    text = re.sub(r"@[\w.]+", " ", type_text).replace("?", "").strip()
    text = re.sub(r"<.*>", "", text).strip()
    array = text.endswith("[]")
    simple = text.removesuffix("[]").strip().split(".")[-1]
    return simple + ("[]" if array else "")


def kind(type_text):
    return KINDS.get(normalised(type_text))


def item(option):
    parts = str(option or "").split("|")
    if len(parts) != 3 or not parts[1]:
        raise InputError(f"no_key_algorithm: option {option!r} is not Type|name|provider")
    return parts


def key_algorithm(option):
    return item(option)[1].split("/")[0]


def expression(parameter, scope, side="after"):
    """`side` picks the provider a key pair is decoded by: another provider's key class is converted at every init, a cost on one side only."""
    literal = LITERALS.get(normalised(parameter.type))
    if literal is not None:
        return literal
    found = kind(parameter.type)
    if found is None:
        raise InputError(f"unsupported_parameter: {parameter.name}: {parameter.type}")
    if found in PAIR_MEMBERS:
        if scope.key_size is None:
            raise InputError(f"missing_input: keySize for {parameter.name}, none from {scope.input_source}")
        kind_of, name, provider = item(scope.option)
        decoder = item(scope.current if side == "before" else scope.option)[2]
        return f'ScopeKeys.pair("{kind_of}", "{name}", "{provider}", {scope.key_size}, "{decoder}"){PAIR_MEMBERS[found]}'
    if found == "key":
        if scope.key_size is None:
            raise InputError(f"missing_input: keySize for {parameter.name}, none from {scope.input_source}")
        return f'ScopeInputs.secretKey("{key_algorithm(scope.option)}", {scope.key_size}, {SEED + 1})'
    if scope.input_size is None:
        raise InputError(f"missing_input: inputSize for {parameter.name}, none from {scope.input_source}")
    return f"ScopeInputs.{found}({scope.input_size}, {SEED})"
