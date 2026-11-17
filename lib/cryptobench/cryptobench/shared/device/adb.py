"""The device half of pipeline.py --device: adb, the APK install, an instrumentation run and its report."""
import os, re, subprocess

from cryptobench.shared.device import timeouts
from cryptobench.shared import paths
from cryptobench.shared.errors.coded import Coded

PACKAGE = paths.DeviceDirs.PACKAGE
RUNNER = "androidx.benchmark.junit4.AndroidBenchmarkRunner"
# androidx falls back to MethodTracing when a case's ProfilerConfig is null, so "profiling: none" needs
# the default set to None; a case asking for a profiler still gets one.
NO_DEFAULT_PROFILER = ["-e", "androidx.benchmark.profiling.mode", "None"]
PASSED = re.compile(r"^OK \(\d+ tests?\)", re.M)
ONE_PASSED = re.compile(r"^OK \(1 test\)", re.M)


class DeviceError(Coded):
    pass


class DeviceLost(DeviceError):
    """The adb transport is gone, whichever call met it; the session waits for the device instead of failing that call's case."""


# adb's own words when the transport, not the command, failed
LOST = re.compile(r"device unauthorized|device offline|device '[^']*' not found|device not found|no devices/emulators found|"
                  r"error: closed|cannot connect to daemon|daemon not running|failed to start daemon|protocol fault|adb server")


def lost(text):
    found = LOST.search(text or "")
    return found.group(0) if found else None


def lost_line(arguments, reason):
    return f"device_lost: adb {' '.join(map(str, arguments))[:200]}: {reason}"


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
        self.environment = paths.android_env()
        self.adb = paths.platform_tools() / "adb"

    def raw(self, *arguments):
        return timeouts.run("adb", [str(self.adb), *arguments], capture_output=True, text=True)

    def run(self, *arguments, check=True):
        result = self.raw(*arguments)
        if result.returncode != 0 and (reason := lost(result.stderr or result.stdout)):
            raise DeviceLost(lost_line(arguments, reason))
        if check and result.returncode != 0:
            raise DeviceError(f"adb {' '.join(arguments)}: {(result.stderr or result.stdout).strip()}")
        return result

    def shell(self, command):
        return self.run("shell", command).stdout

    def state(self):
        """adb get-state's answer, '' when there is none; never raises, so a wait can poll it."""
        try:
            result = self.raw("get-state")
        except timeouts.StepTimeout:
            return ""
        return result.stdout.strip() if result.returncode == 0 else ""

    def attached(self, step):
        state = self.state()
        if state != "device":
            raise DeviceLost(lost_line(("get-state", "after", step), state or "no answer"))

    def connect(self):
        if not self.adb.is_file():
            raise DeviceError(f"missing_file: {self.adb} (set ANDROID_HOME)")
        selection = selection_error(self.run("devices").stdout, os.environ.get("ANDROID_SERIAL"))
        if selection:
            raise DeviceError(selection)
        state = self.raw("get-state")
        if state.stdout.strip() != "device":
            raise DeviceError(f"no_device: adb get-state: {(state.stderr or state.stdout).strip()}")
        sdk = self.shell("getprop ro.build.version.sdk").strip()
        if not sdk.isdigit():
            raise DeviceError(f"no_sdk: getprop ro.build.version.sdk printed {sdk!r}")
        dirs = paths.DeviceDirs(int(sdk))
        self.files, self.media, self.data = str(dirs.plan), str(dirs.output), str(dirs.benchmark_data)

    def identity(self):
        """The runtime fields device_id reads, by getprop: Build.MODEL and Build.FINGERPRINT read these properties."""
        return {"sdkInt": int(self.shell("getprop ro.build.version.sdk").strip()),
                "model": self.shell("getprop ro.product.model").strip(),
                "fingerprint": self.shell("getprop ro.build.fingerprint").strip()}

    def boot_id(self):
        """The kernel's id of this boot: a restart gives a new one."""
        return self.shell(f"cat {paths.DeviceDirs.BOOT_ID}").strip()

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
            result = timeouts.run(step, command, capture_output=True, text=True)
            if result.returncode != 0 and (reason := lost(result.stderr)):
                raise DeviceLost(lost_line(command[1:4], reason))
            output = result.stdout
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
        if not PASSED.search(output):
            # a dropped transport cuts the output short; a failed test leaves the device attached
            self.attached(f"am instrument {test_class}")
            if self.stacktrace:
                print(output)
        return output

    def pull(self, remote, local):
        result = self.run("pull", remote, str(local), check=False)
        if result.returncode != 0:
            reason = (result.stderr or result.stdout).strip()
            if "Permission denied" in reason:
                reason += "; shell reaches the app's files only in a directory the app created"
            raise DeviceError(f"adb pull {remote}: {reason}")

    def push_files(self, *files):
        self.run("push", *map(str, files), f"{self.files}/")

    def report(self, output):
        return instrumentation_report(output)

    def force_stop(self):
        self.run("shell", f"am force-stop {PACKAGE}", check=False)
