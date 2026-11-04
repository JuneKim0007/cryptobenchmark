"""The device half of pipeline.py --device: adb, the instrumentation classes, and the files they leave."""
import os, pathlib, re, subprocess

import yaml

import timeouts

PACKAGE = "io.github.junekim0007.cryptobench"
RUNNER = "androidx.benchmark.junit4.AndroidBenchmarkRunner"
PLAN_DIRECTORY = "cryptobench"   # DeviceDirectory.NAME
CPU_PINS = "cpu-pins.yaml"   # CorePins.FILE
SCOPED_INTEROP = "scoped-interop.yaml"   # ScopeInteropFile.FILE
CALL_SITE_VERDICTS = "callsite-verdicts.yaml"   # CallSitePlan.VERDICTS
SCOPE_KEYS = "scope-keys"   # ScopeKeys.FOLDER
# androidx falls back to MethodTracing when a case's ProfilerConfig is null, so "profiling: none" needs
# the default set to None; a case asking for a profiler still gets one.
NO_DEFAULT_PROFILER = ["-e", "androidx.benchmark.profiling.mode", "None"]
# androidx's CPU event capture is internal; only this launch argument adds it (JetpackConfig.counterMismatch).
CPU_EVENTS = ["-e", "androidx.benchmark.cpuEventCounter.enable", "true"]
PASSED = re.compile(r"^OK \(\d+ tests?\)", re.M)
ONE_PASSED = re.compile(r"^OK \(1 test\)", re.M)


THROTTLE_SLEEP = "androidx.benchmark.thermalThrottle.sleepDurationSeconds"


def measure_arguments(suppress, metrics, throttle_sleep=None):
    return (NO_DEFAULT_PROFILER + (["-e", "androidx.benchmark.suppressErrors", suppress] if suppress else [])
            + (CPU_EVENTS if "CPU_EVENTS" in metrics else []) + (["-e", THROTTLE_SLEEP, str(throttle_sleep)] if throttle_sleep is not None else []))


class DeviceError(Exception):
    pass


def directories(sdk):
    """(plan directory, androidx output directory) at this API level; paired with DeviceDirectory.kt."""
    if sdk >= 29:
        media = f"/sdcard/Android/media/{PACKAGE}"
        return f"{media}/{PLAN_DIRECTORY}", media
    data = f"/sdcard/Android/data/{PACKAGE}"
    return f"{data}/files/{PLAN_DIRECTORY}", f"{data}/cache"


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


def selection_error(listing, serial):
    """The coded line when `adb devices` output leaves a bare adb command ambiguous or its target absent; else None."""
    attached = [line.split("\t")[0] for line in listing.splitlines() if "\t" in line]
    if serial and serial not in attached:
        return f"device_not_attached: ANDROID_SERIAL={serial}; attached: {', '.join(attached) or 'none'}"
    if not serial and len(attached) > 1:
        return f"several_devices: {', '.join(attached)}; set ANDROID_SERIAL to one"
    return None


class Device:

    def __init__(self, root, stream, stacktrace):
        self.root, self.stream, self.stacktrace = root, stream, stacktrace
        self.environment = dict(os.environ, ANDROID_HOME=str(android_home()))
        self.adb = android_home() / "platform-tools/adb"

    def run(self, *arguments, check=True):
        result = timeouts.run("adb", [str(self.adb), *arguments], capture_output=True, text=True)
        if check and result.returncode != 0:
            raise DeviceError(f"adb {' '.join(arguments)}: {(result.stderr or result.stdout).strip()}")
        return result

    def shell(self, command):
        return self.run("shell", command).stdout

    def connect(self):
        if not self.adb.is_file():
            raise DeviceError(f"missing_file: {self.adb} (set ANDROID_HOME)")
        selection = selection_error(self.run("devices").stdout, os.environ.get("ANDROID_SERIAL"))
        if selection:
            raise DeviceError(selection)
        state = self.run("get-state", check=False)
        if state.stdout.strip() != "device":
            raise DeviceError(f"no_device: adb get-state: {(state.stderr or state.stdout).strip()}")
        sdk = self.shell("getprop ro.build.version.sdk").strip()
        if not sdk.isdigit():
            raise DeviceError(f"no_sdk: getprop ro.build.version.sdk printed {sdk!r}")
        self.files, self.media = directories(int(sdk))
        self.data = f"{self.media}/{PACKAGE}-benchmarkData.json"

    def identity(self):
        """The runtime fields device_id reads, by getprop: Build.MODEL and Build.FINGERPRINT read these properties."""
        return {"sdkInt": int(self.shell("getprop ro.build.version.sdk").strip()),
                "model": self.shell("getprop ro.product.model").strip(),
                "fingerprint": self.shell("getprop ro.build.fingerprint").strip()}

    def install(self, properties=()):
        command = [str(self.root / "gradlew"), "-p", str(self.root), *properties, ":android:installRelease", ":android:installReleaseAndroidTest"]
        if self.stream:
            if timeouts.run("install", command, env=self.environment).returncode != 0:
                raise DeviceError("gradle install failed; rerun without --stream for a filtered message")
            return
        result = timeouts.run("install", command, capture_output=True, text=True, env=self.environment)
        if result.returncode != 0:
            output = (result.stdout + result.stderr).splitlines()
            if self.stacktrace:
                print("\n".join(output))
            reason = output[output.index("* What went wrong:") + 1:] if "* What went wrong:" in output else output[-5:]
            raise DeviceError("gradle install failed:\n" + "\n".join(line for line in reason[:10] if line.strip() and not line.startswith("* Try:")))

    def instrument(self, test_class, *arguments, step="instrument"):
        command = [str(self.adb), "shell", "am", "instrument", "-w", "-r", "-e", "class", f"{PACKAGE}.{test_class}",
                   *arguments, f"{PACKAGE}.test/{RUNNER}"]
        if not self.stream:
            output = timeouts.run(step, command, capture_output=True, text=True).stdout
        else:
            process, lines, shown = subprocess.Popen(command, stdout=subprocess.PIPE, text=True), [], set()
            with timeouts.watched(step, process, command):
                for line in process.stdout:
                    if line.startswith(("INSTRUMENTATION_STATUS: test=", "INSTRUMENTATION_STATUS: stack=", "Tests run:", "OK (")) and line not in shown:
                        print(f"  {line.rstrip()}")
                        shown.add(line)
                    lines.append(line)
                process.wait()
            output = "".join(lines)
        if self.stacktrace and not PASSED.search(output):
            print(output)
        return output

    def pull(self, remote, local):
        result = self.run("pull", remote, str(local), check=False)
        if result.returncode != 0:
            reason = (result.stderr or result.stdout).strip()
            if "Permission denied" in reason:
                reason += "; shell reaches the app's files only in a directory the app created"
            raise DeviceError(f"adb pull {remote}: {reason}")

    def probe(self, discovery, arguments=()):
        # The app must create its own directory: one made by shell is not writable by the app's uid.
        self.shell(f"rm -rf {self.files}")
        self.shell(f"rm -f {self.media}/*-benchmarkData.json")
        output = self.instrument("DeviceProbe", *arguments)
        if "OK (1 test)" not in output:
            raise DeviceError("DeviceProbe failed on the device:\n" + instrumentation_report(output))
        self.pull(f"{self.files}/.", discovery)

    def push_files(self, *files):
        self.run("push", *map(str, files), f"{self.files}/")

    def push_plan(self, *files):
        self.push_files(*files)
        # Without androidx.benchmark's gradle plugin nothing AOT-compiles the APKs, and Jetpack fails
        # every case with NOT-AOT-COMPILED.
        for package in (PACKAGE, f"{PACKAGE}.test"):
            compiled = self.shell(f"cmd package compile -f -m speed {package}")
            if "Success" not in compiled:
                raise DeviceError(f"AOT compile {package}: {compiled.strip()}")

    def report(self, output):
        return instrumentation_report(output)

    def force_stop(self):
        self.run("shell", f"am force-stop {PACKAGE}", check=False)

    def clear_outputs(self, plan_files=()):
        """androidx's outputs and the plan directory's per-run files, so nothing of an earlier process is pulled as this one's."""
        planned = " ".join(f"{self.files}/{name}" for name in (*plan_files, CPU_PINS))
        self.shell(f"rm -f {self.media}/*-benchmarkData.json {self.media}/*.perfetto-trace {self.media}/*.trace {planned}")

    def pull_pins(self, into):
        pins = into / CPU_PINS
        pins.unlink(missing_ok=True)
        self.run("pull", f"{self.files}/{CPU_PINS}", str(pins), check=False)

    def pull_plan(self, preparation):
        preparation.mkdir(parents=True, exist_ok=True)
        self.pull(f"{self.files}/prepared.yaml", preparation / "prepared.yaml")
        self.pull(f"{self.files}/skipped.yaml", preparation / "skipped.yaml")

    def check_scopes(self, into):
        """ScopedInterop in its own process: every scope's verdict, before any scope is measured."""
        interop = into / SCOPED_INTEROP
        interop.unlink(missing_ok=True)
        into.mkdir(parents=True, exist_ok=True)
        self.shell(f"rm -f {self.files}/{SCOPED_INTEROP} {self.files}/{CALL_SITE_VERDICTS}")
        self.shell(f"rm -rf {self.files}/callsite-*/ {self.files}/{SCOPE_KEYS}")
        output = self.instrument("ScopedInterop")
        if not ONE_PASSED.search(output):
            raise DeviceError("ScopedInterop failed on the device:\n" + instrumentation_report(output))
        self.pull(f"{self.files}/{SCOPED_INTEROP}", interop)
        return interop

    def pull_call_sites(self, into):
        """The call sites' verdicts, and the prepared.yaml of each folder a prepared one names."""
        verdicts = into / CALL_SITE_VERDICTS
        self.pull(f"{self.files}/{CALL_SITE_VERDICTS}", verdicts)
        folders = {v["folder"] for v in (yaml.safe_load(verdicts.read_text()) or {}).values() if v.get("status") == "prepared"}
        for folder in sorted(folders):
            (into / folder).mkdir(parents=True, exist_ok=True)
            self.pull(f"{self.files}/{folder}/prepared.yaml", into / folder / "prepared.yaml")
        return verdicts
