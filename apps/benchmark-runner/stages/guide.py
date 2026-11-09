"""After effective.yaml says what runs: picks exactly those items from the implementation guide, beside it, for preparation."""
import pathlib
import sys

import yaml

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3] / "lib/cryptobench"))
from cryptobench.catalogue.guide_items import guide_items  # noqa: E402

NAME = "guide.yaml"


def file_beside(effective):
    return pathlib.Path(effective).with_name(NAME)


def platform(runtime):
    """The guide's name for where this capture ran: android-<sdk>, else jdk-<major> of a host JVM."""
    if runtime.get("sdkInt"):
        return f"android-{runtime['sdkInt']}"
    major = str(runtime.get("javaVersion") or "").split(".")[0]
    return f"jdk-{major}" if major else None


def fallbacks(document):
    """One line per provider the guide has no exact build for, whatever number of items it has here."""
    used = {}
    for provider, types in document["items"].items():
        for names in types.values():
            for item in names.values():
                if not item.get("exactBuild"):
                    used[provider] = item.get("build")
    return [f"guide_build_fallback: {provider} has no row of its own for this build; using {build}" for provider, build in used.items()]


def write(effective, capture):
    runtime = yaml.safe_load(pathlib.Path(capture).read_text()).get("runtime") or {}
    document = guide_items(yaml.safe_load(pathlib.Path(effective).read_text()), platform(runtime))
    for line in fallbacks(document):
        print(f"warning: {line}")
    written = file_beside(effective)
    written.write_text(yaml.safe_dump(document, sort_keys=False))
    return written
