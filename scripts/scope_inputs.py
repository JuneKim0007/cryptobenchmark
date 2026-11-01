"""Which parameter types a scope wrapper can synthesise, and the ScopeInputs call that builds each."""
import re

SEED = 7
# kind per normalised type; every other type is unsupported_parameter.
KINDS = {"byte[]": "bytes", "ByteArray": "bytes", "String": "text", "CharSequence": "text",
         "char[]": "chars", "CharArray": "chars", "SecretKey": "key", "Key": "key", "SecretKeySpec": "key"}
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


def key_algorithm(option):
    parts = str(option or "").split("|")
    if len(parts) != 3 or not parts[1]:
        raise InputError(f"no_key_algorithm: option {option!r} is not Type|name|provider")
    return parts[1].split("/")[0]


def expression(parameter, scope):
    found = kind(parameter.type)
    if found is None:
        raise InputError(f"unsupported_parameter: {parameter.name}: {parameter.type}")
    if found == "key":
        if scope.key_size is None:
            raise InputError(f"missing_input: keySize for {parameter.name}")
        return f'ScopeInputs.secretKey("{key_algorithm(scope.option)}", {scope.key_size}, {SEED + 1})'
    if scope.input_size is None:
        raise InputError(f"missing_input: inputSize for {parameter.name}")
    return f"ScopeInputs.{found}({scope.input_size}, {SEED})"
