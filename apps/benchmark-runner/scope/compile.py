"""Compiles the android test sources with Gradle; returns the compiler's error lines, empty when it passed."""
import os, re

import timeouts
from cryptobench import paths

TASK = ":android:compileReleaseAndroidTestJavaWithJavac"
ERROR = re.compile(r"^(e: |.*\.java:\d+: error: )")


def errors(output, root):
    lines = [line.strip().replace(f"file://{root}/", "").replace(f"{root}/", "") for line in output.splitlines() if ERROR.match(line.strip())]
    return list(dict.fromkeys(lines))[:8]


def gradle(root):
    command = [str(root / "gradlew"), "-p", str(root), TASK, "-q"]
    result = timeouts.run("compile", command, capture_output=True, text=True, env=dict(os.environ, ANDROID_HOME=str(paths.android_home())))
    if result.returncode == 0:
        return []
    output = result.stdout + result.stderr
    return errors(output, root) or [line for line in output.splitlines() if line.strip()][-5:]
