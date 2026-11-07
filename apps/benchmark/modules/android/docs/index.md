# android

```
apps/benchmark/modules/android/.gitignore : ignores /build
apps/benchmark/modules/android/build.gradle : app module: SDK, NDK and CMake versions, androidx benchmark dependencies, -PbundledArtifacts implementation dependencies, release test build type
apps/benchmark/modules/android/docs/harness.md : instrumentation harness, device plan, core pinning
apps/benchmark/modules/android/docs/index.md : this map
apps/benchmark/modules/android/docs/scoped.md : scoped interop check: generated scopes, original against patched
apps/benchmark/modules/android/proguard-rules.pro : Android Studio template, all rules commented out
apps/benchmark/modules/android/src/androidTest/java/.gitignore : ignores the generated scoped/ sources
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/Bundled.kt : installs the bundledProviders of a pushed effective.yaml into the process
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CaseFilter.kt : the `case` argument: one id or an ordered comma list; absent keeps every case
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CorePin.kt : pins the measuring thread to one core and restores on close
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CorePins.kt : appends one line per pinned case to cpu-pins.yaml
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CryptoBenchmark.kt : parameterised Jetpack measurement per timed case
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/DeviceDirectory.kt : the plan directory on the device, by API level
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/DevicePlan.kt : installs effective.yaml's bundled providers; prepares and checks the plan on the device from pushed files; its skips; `CaseFilter` narrows the timed cases
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/DeviceProbe.kt : installs the argument's bundled providers; writes this device's capture and trial via discovery
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/EndToEndCheck.kt : the end-to-end check on the device: every planned case once through Jetpack under the dry run, all in one process; check.yaml
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/EnergyDryBenchmark.kt : parameterised dry energy run per dry case
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/InteropCheck.kt : installs bundled providers; runs the pushed interop_plan.yaml into interop.yaml
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/JetpackCase.kt : base of a Jetpack-timed case: its rule, the counter check, the pin, the timed loop; once() for the check, its output to the hook
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/JetpackConfig.kt : CaseSettings to MicrobenchmarkConfig; reportable metrics, CPU event counter argument check
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/PassArguments.kt : the run.passes pass and samples the host names, applied over a case's settings
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/PinnedCase.kt : one timed case under its cpu pin and energy setting
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/SampledAllocations.kt : allocation counting inside the timed phase for an allocation pass
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/Scope.kt : one scope's before and after calls and its interop check
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeCatalog.kt : loads the generated GeneratedScopes catalog
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeCheck.kt : calls both variants once and runs the interop check
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeInputs.kt : seeded bytes, text, files and secret keys for generated scopes
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeInteropFile.kt : writes scoped-interop.yaml
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeKeys.kt : key pairs for generated scopes: from the key planner once per run, kept on the device, decoded per side
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopedInterop.kt : the scope check in its own process: every scope's verdict into scoped-interop.yaml
apps/benchmark/modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/TraceWindowMarker.kt : WindowMarker over android.os.Trace sections
apps/benchmark/modules/android/src/main/AndroidManifest.xml : app manifest (allowBackup false)
apps/benchmark/modules/android/src/main/cpp/CMakeLists.txt : builds shared library affinity
apps/benchmark/modules/android/src/main/cpp/affinity.c : JNI sched_getaffinity and sched_setaffinity for cores 0..63
apps/benchmark/modules/android/src/main/kotlin/io/github/junekim0007/cryptobench/Affinity.kt : Kotlin binding for libaffinity.so
apps/benchmark/modules/android/src/main/res/values/strings.xml : app_name "crypto benchmark"
```
