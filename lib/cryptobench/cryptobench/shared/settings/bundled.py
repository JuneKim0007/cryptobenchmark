"""providers.bundled of global.yaml: its entries checked for authored.read by bundled_rule and for duplicates, the build property of the app or the host CLI, the DeviceProbe argument, effective.yaml's record and the check against it."""
import json, shlex
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.errors.input_error import InputError
from cryptobench.shared.settings import bundled_rule


KEY = "bundledProviders"   # contract's BundledProvider.KEY, the effective.yaml key


class BundledError(InputError):
    pass


def entries(document, global_file):
    providers = document.get("providers")
    if providers is None:
        return []
    if not isinstance(providers, dict):
        raise BundledError(f"wrong_type: {global_file}: providers")
    if unknown := [key for key in providers if key != "bundled"]:
        raise BundledError(f"unknown_keys: {global_file}: providers [{', '.join(map(str, unknown))}], known [bundled]")
    bundled = providers.get("bundled")
    if bundled is None:
        return []
    if not isinstance(bundled, list):
        raise BundledError(f"wrong_type: {global_file}: providers.bundled, expected a list of {{artifact, create, alias?}}")
    for index, entry in enumerate(bundled):
        if refused := bundled_rule.problem(entry, f"providers.bundled[{index}]"):
            raise BundledError(f"{refused[0]}: {global_file}: {refused[1]}")
    checked = [{key: value for key, value in entry.items() if value is not None} for entry in bundled]
    for key in ("artifact", "alias"):
        _unique([entry[key] for entry in checked if key in entry], f"duplicate_{key}", global_file)
    return checked


def _unique(values, code, global_file):
    repeated = list(dict.fromkeys(value for value in values if values.count(value) > 1))
    if repeated:
        raise BundledError(f"{code}: {global_file}: [{', '.join(repeated)}] at providers.bundled")


def gradle_properties(bundled):
    return [f"-PbundledArtifacts={','.join(entry['artifact'] for entry in bundled)}"] if bundled else []


def instrumentation_arguments(bundled):
    # adb shell joins its arguments into one device shell line, so the value is quoted for that shell.
    return ["-e", KEY, shlex.quote(json.dumps({KEY: bundled}))] if bundled else []


def artifacts(effective):
    """effective.yaml's bundled providers, artifact by alias."""
    return {b.get("alias"): b["artifact"] for b in effective.get(KEY) or []}


def recorded(effective_file):
    return read_yaml(effective_file).get(KEY) or []


def check_effective(effective_file, bundled):
    found = recorded(effective_file)
    if found != bundled:
        raise BundledError(f"bundled_mismatch: {effective_file} records {found}, the app was built with {bundled}")
