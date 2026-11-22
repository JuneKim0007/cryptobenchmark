"""One providers.bundled entry checked as config's ProvidersDocument and contract's BundledProvider check it, in their order."""
import re
import unicodedata

FIELDS = ("artifact", "create", "alias")
# Java's \s, which Kotlin's Regex means; Python's \s also takes Unicode spaces
_SPACE = " \t\n\x0b\f\r"
_ARTIFACT = re.compile(rf"[^:,{_SPACE}]+:[^:,{_SPACE}]+:[^:,{_SPACE}]+")


def problem(entry, at):
    """The first refusal for entry at its path as (code, detail); None when Kotlin accepts it."""
    if not isinstance(entry, dict):
        return "wrong_type", f"{at}, expected {{artifact, create, alias?}}"
    unknown = [key for key in entry if key not in FIELDS]
    if unknown:
        return "unknown_keys", f"{at} [{', '.join(map(str, unknown))}], known [{', '.join(FIELDS)}]"
    for key in ("artifact", "create"):
        if entry.get(key) is None:
            return "missing_field", f"{key} at {at}"
        if not isinstance(entry[key], str):
            return "wrong_type", f"{key} at {at}"
    alias = entry.get("alias")
    if alias is not None and not isinstance(alias, str):
        return "wrong_type", f"alias at {at}"
    if not _ARTIFACT.fullmatch(entry["artifact"]):
        return "invalid_artifact", f"{entry['artifact']}, expected group:name:version at {at}"
    if not _create(entry["create"]):
        return "invalid_create", f"{entry['create']}, expected fully.qualified.Class or fully.qualified.Class#staticFactory at {at}"
    if alias is not None and (not alias or any(c in _SPACE for c in alias)):
        return "invalid_alias", f"'{alias}', expected a non-blank name without whitespace at {at}"
    return None


def _create(text):
    """Kotlin's ID(.ID)+(#ID)? where ID is [\\p{L}_$][\\p{L}\\p{N}_$]*; Python's re has no \\p{L}, so by category."""
    type_name, *factory = text.split("#")
    parts = type_name.split(".")
    return len(factory) <= 1 and len(parts) >= 2 and all(map(_identifier, parts + factory))


def _identifier(word):
    return bool(word) and _part(word[0], "L") and all(_part(c, "LN") for c in word[1:])


def _part(character, categories):
    return character in "_$" or unicodedata.category(character)[0] in categories
