"""providers.bundled of global.yaml: the digest's raw read, the app build property, the DeviceProbe argument, the check against effective.yaml."""
import json, shlex

import yaml

KEY = "bundledProviders"   # BundledProviders.KEY and the effective.yaml key


class BundledError(Exception):
    pass


def read(global_file):
    document = yaml.safe_load(global_file.read_text()) or {}
    providers = document.get("providers") or {}
    if not isinstance(providers, dict):
        raise BundledError(f"wrong_type: providers in {global_file}")
    bundled = providers.get("bundled") or []
    if not isinstance(bundled, list) or not all(isinstance(entry, dict) and isinstance(entry.get("artifact"), str) for entry in bundled):
        raise BundledError(f"wrong_type: providers.bundled in {global_file}, expected a list of {{artifact, create, alias?}}")
    return [{key: value for key, value in entry.items() if value is not None} for entry in bundled]


def gradle_properties(bundled):
    return [f"-PbundledArtifacts={','.join(entry['artifact'] for entry in bundled)}"] if bundled else []


def instrumentation_arguments(bundled):
    # adb shell joins its arguments into one device shell line, so the value is quoted for that shell.
    return ["-e", KEY, shlex.quote(json.dumps({KEY: bundled}))] if bundled else []


def check_effective(effective_file, bundled):
    recorded = (yaml.safe_load(effective_file.read_text()) or {}).get(KEY) or []
    if recorded != bundled:
        raise BundledError(f"bundled_mismatch: {effective_file} records {recorded}, the app was built with {bundled}")
