"""The known answers a --check run checks against: the guide's vectors filled per provider, plus the vectors global.yaml's selection.knownVectors names, resolved against global.yaml."""

from cryptobench.shared.log.warn import warn
from cryptobench.shared import paths
from cryptobench.shared.catalogue import vectors
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.device.capture import platform
from cryptobench.shared.document.dump import dump_yaml


def user_vectors(configuration):
    """selection.knownVectors of global.yaml, against that file; a test set's vectors are read only by --check."""
    named = (read_yaml(configuration).get("selection") or {}).get("knownVectors")
    return paths.against(configuration, named) if named else None


def write_known_answers(effective, capture, configuration):
    runtime = read_yaml(capture).get("runtime") or {}
    document, warnings = vectors.filled(read_yaml(effective), platform(runtime), user_vectors(configuration))
    for line in warnings:
        warn(line)
    written = paths.Configuration.holding(effective).known_answers
    written.write_text(dump_yaml(document))
    return written
