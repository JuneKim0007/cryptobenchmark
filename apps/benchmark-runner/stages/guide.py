"""After effective.yaml says what runs: picks exactly those items from the implementation guide, beside it, for preparation."""
import pathlib

from cryptobench.shared import paths
from cryptobench.shared.catalogue.guide_items import guide_items
from cryptobench.shared.catalogue import vectors
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.device.capture import platform
from cryptobench.shared.document.dump import dump_yaml

def file_beside(effective):
    return paths.Configuration(pathlib.Path(effective).parent).guide


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
        print(f"warning: {line}")
    written = file_beside(effective)
    written.write_text(dump_yaml(document))
    return written


def user_vectors(configuration):
    """selection.knownVectors of global.yaml, against that file; a test set's vectors are read only by --check."""
    named = (read_yaml(configuration).get("selection") or {}).get("knownVectors")
    return paths.against(configuration, named) if named else None


def write_known_answers(effective, capture, configuration):
    runtime = read_yaml(capture).get("runtime") or {}
    document, warnings = vectors.filled(read_yaml(effective), platform(runtime), user_vectors(configuration))
    for line in warnings:
        print(f"warning: {line}")
    written = paths.Configuration(pathlib.Path(effective).parent).known_answers
    written.write_text(dump_yaml(document))
    return written
