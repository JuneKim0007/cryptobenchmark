"""The device half of pipeline.py --device: adb, the instrumentation classes, and the files they leave."""
import os, pathlib, re, subprocess

PACKAGE = "io.github.junekim0007.cryptobench"
RUNNER = "androidx.benchmark.junit4.AndroidBenchmarkRunner"
FILES = f"/sdcard/Android/data/{PACKAGE}/files/cryptobench"   # DevicePlan.directory
MEDIA = f"/sdcard/Android/media/{PACKAGE}"                     # androidx.benchmark's output directory
DATA = f"{MEDIA}/{PACKAGE}-benchmarkData.json"
CPU_PINS = "cpu-pins.yaml"   # CorePins.FILE
# androidx falls back to MethodTracing when a case's ProfilerConfig is null, so "profiling: none" needs
# the default set to None; a case asking for a profiler still gets one.
NO_DEFAULT_PROFILER = ["-e", "androidx.benchmark.profiling.mode", "None"]


class DeviceError(Exception):
    pass


def android_home():
    return pathlib.Path(os.environ.get("ANDROID_HOME") or pathlib.Path.home() / "Library/Android/sdk")


def instrumentation_report(output):
    stacks = {}
    for line in output.splitlines():
        if line.startswith("INSTRUMENTATION_STATUS: stack="):
            first = line[len("INSTRUMENTATION_STATUS: stack="):]
            stacks[first] = stacks.get(first, 0) + 1
    lines = [f"  {first}" + (f" (x{count})" if count > 1 else "") for first, count in stacks.items()]
    lines += [line for line in output.splitlines() if line.startswith(("Tests run:", "INSTRUMENTATION_RESULT: shortMsg=", "INSTRUMENTATION_FAILED"))]
    return "\n".join(lines or [line for line in output.splitlines() if line.strip()][-5:])


class Device:

    def __init__(self, root, stream, stacktrace):
        self.root, self.stream, self.stacktrace = root, stream, stacktrace
        self.environment = dict(os.environ, ANDROID_HOME=str(android_home()))
        self.adb = android_home() / "platform-tools/adb"

    def run(self, *arguments, check=True):
        result = subprocess.run([str(self.adb), *arguments], capture_output=True, text=True)
        if check and result.returncode != 0:
            raise DeviceError(f"adb {' '.join(arguments)}: {(result.stderr or result.stdout).strip()}")
        return result

    def shell(self, command):
        return self.run("shell", command).stdout

    def connect(self):
        if not self.adb.is_file():
            raise DeviceError(f"missing_file: {self.adb} (set ANDROID_HOME)")
        state = self.run("get-state", check=False)
        if state.stdout.strip() != "device":
            raise DeviceError(f"no_device: adb get-state: {(state.stderr or state.stdout).strip()}")

    def install(self):
        command = [str(self.root / "gradlew"), "-p", str(self.root), ":android:installRelease", ":android:installReleaseAndroidTest"]
        if self.stream:
            if subprocess.run(command, env=self.environment).returncode != 0:
                raise DeviceError("gradle install failed; rerun without --stream for a filtered message")
            return
        result = subprocess.run(command, capture_output=True, text=True, env=self.environment)
        if result.returncode != 0:
            output = (result.stdout + result.stderr).splitlines()
            if self.stacktrace:
                print("\n".join(output))
            reason = output[output.index("* What went wrong:") + 1:] if "* What went wrong:" in output else output[-5:]
            raise DeviceError("gradle install failed:\n" + "\n".join(line for line in reason[:10] if line.strip() and not line.startswith("* Try:")))

    def instrument(self, test_class, *arguments):
        command = [str(self.adb), "shell", "am", "instrument", "-w", "-r", "-e", "class", f"{PACKAGE}.{test_class}",
                   *arguments, f"{PACKAGE}.test/{RUNNER}"]
        if not self.stream:
            output = subprocess.run(command, capture_output=True, text=True).stdout
        else:
            process, lines, shown = subprocess.Popen(command, stdout=subprocess.PIPE, text=True), [], set()
            for line in process.stdout:
                if line.startswith(("INSTRUMENTATION_STATUS: test=", "INSTRUMENTATION_STATUS: stack=", "Tests run:", "OK (")) and line not in shown:
                    print(f"  {line.rstrip()}")
                    shown.add(line)
                lines.append(line)
            process.wait()
            output = "".join(lines)
        if self.stacktrace and not re.search(r"^OK \(\d+ tests?\)", output, re.M):
            print(output)
        return output

    def pull(self, remote, local):
        result = self.run("pull", remote, str(local), check=False)
        if result.returncode != 0:
            reason = (result.stderr or result.stdout).strip()
            if "Permission denied" in reason:
                reason += "; shell reads the app's files through group ext_data_rw, which only a directory the app created carries"
            raise DeviceError(f"adb pull {remote}: {reason}")

    def probe(self, discovery):
        # The app must create its own directory: one made by shell is not writable by the app's uid.
        self.shell(f"rm -rf {FILES}")
        self.shell(f"rm -f {MEDIA}/*-benchmarkData.json")
        output = self.instrument("DeviceProbe")
        if "OK (1 test)" not in output:
            raise DeviceError("DeviceProbe failed on the device:\n" + instrumentation_report(output))
        self.pull(f"{FILES}/.", discovery)

    def push_plan(self, *files):
        self.run("push", *map(str, files), f"{FILES}/")
        # Without androidx.benchmark's gradle plugin nothing AOT-compiles the APKs, and Jetpack fails
        # every case with NOT-AOT-COMPILED.
        for package in (PACKAGE, f"{PACKAGE}.test"):
            compiled = self.shell(f"cmd package compile -f -m speed {package}")
            if "Success" not in compiled:
                raise DeviceError(f"AOT compile {package}: {compiled.strip()}")

    def measure(self, suppress, data, preparation):
        self.shell(f"rm -f {MEDIA}/*-benchmarkData.json {MEDIA}/*.perfetto-trace {MEDIA}/*.trace {FILES}/prepared.yaml {FILES}/skipped.yaml {FILES}/{CPU_PINS}")
        arguments = NO_DEFAULT_PROFILER + (["-e", "androidx.benchmark.suppressErrors", suppress] if suppress else [])
        output = self.instrument("CryptoBenchmark", *arguments)
        if not re.search(r"^OK \(\d+ tests?\)", output, re.M):
            counted = re.search(r"^Tests run: (\d+),\s+Failures: (\d+)", output, re.M)
            if not counted or counted.group(1) == counted.group(2):
                raise DeviceError("CryptoBenchmark failed on the device:\n" + instrumentation_report(output))
            print("warning: CryptoBenchmark: " + instrumentation_report(output).replace("\n", "\nwarning: "))
        for stale in (data, preparation / "prepared.yaml", preparation / "skipped.yaml"):
            stale.unlink(missing_ok=True)
        data.parent.mkdir(parents=True, exist_ok=True)
        preparation.mkdir(parents=True, exist_ok=True)
        self.pull(DATA, data)
        self.pull_plan(preparation)
        pins = data.parent / CPU_PINS
        pins.unlink(missing_ok=True)
        self.run("pull", f"{FILES}/{CPU_PINS}", str(pins), check=False)

    def pull_plan(self, preparation):
        preparation.mkdir(parents=True, exist_ok=True)
        self.pull(f"{FILES}/prepared.yaml", preparation / "prepared.yaml")
        self.pull(f"{FILES}/skipped.yaml", preparation / "skipped.yaml")
