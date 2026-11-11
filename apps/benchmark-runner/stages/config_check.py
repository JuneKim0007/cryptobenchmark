"""The parse-only check of a global.yaml and its test set before any build: the real parsers, through CheckConfigKt."""
import functools
import pathlib
import shlex

import gradle_runner
from cryptobench.shared.document.document import parse_yaml
from cryptobench.shared.errors.coded import Coded


class ConfigCheckError(Coded):
    pass


def parse_all(files):
    """One {global, testSet, bundled} per file; the first refusal is one ConfigCheckError line."""
    try:
        output = gradle_runner.output_of(shlex.join(map(str, files)), "CheckConfigKt")
    except gradle_runner.ToolFailed as e:
        raise ConfigCheckError(str(e)) from None
    return parse_yaml("\n".join(output), "CheckConfigKt output", shape=list)


# a run reads the answer before the build and again in discover; one Gradle start is enough
@functools.cache
def parsed(global_file):
    return parse_all([pathlib.Path(global_file)])[0]
