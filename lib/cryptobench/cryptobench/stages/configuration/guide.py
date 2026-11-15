"""After effective.yaml says what runs: picks exactly those items from the implementation guide, beside it, for preparation."""

from cryptobench.pipeline.warn import warn
from cryptobench.shared import paths
from cryptobench.shared.catalogue.guide_items import guide_items
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.device.capture import platform
from cryptobench.shared.document.dump import dump_yaml


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
    runtime = read_yaml(capture).get("runtime") or {}
    document = guide_items(read_yaml(effective), platform(runtime))
    for line in fallbacks(document):
        warn(line)
    written = paths.Configuration.holding(effective).guide
    written.write_text(dump_yaml(document))
    return written
