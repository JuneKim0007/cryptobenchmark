# android

```
modules/android/.gitignore : ignores /build
modules/android/build.gradle : app module: SDK, NDK and CMake versions, androidx benchmark dependencies, -PbundledArtifacts implementation dependencies, release test build type
modules/android/docs/harness.md : instrumentation harness, device plan, core pinning
modules/android/docs/index.md : this map
modules/android/docs/scoped.md : scoped benchmark: generated scopes, interop check, before/after measurement
modules/android/proguard-rules.pro : Android Studio template, all rules commented out
modules/android/src/androidTest/java/.gitignore : ignores the generated scoped/ sources
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/Bundled.kt : installs the bundledProviders of a pushed effective.yaml into the process
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CallSitePlan.kt : each swap's call site alone: callsite.yaml's cases prepared from their own effective files, their verdicts into callsite-verdicts.yaml
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CaseFilter.kt : the `case` argument: one id or an ordered comma list; absent keeps every case
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CorePin.kt : pins the measuring thread to one core and restores on close
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CorePins.kt : appends one line per pinned case to cpu-pins.yaml
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CryptoBenchmark.kt : parameterised Jetpack measurement per timed case
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/DeviceDirectory.kt : the plan directory on the device, by API level
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/DevicePlan.kt : installs effective.yaml's bundled providers; prepares and checks the plan on the device from pushed files; `CaseFilter` narrows the timed cases
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/DeviceProbe.kt : installs the argument's bundled providers; writes this device's capture and trial via discovery
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/EnergyDryBenchmark.kt : parameterised dry energy run per dry case
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/InteropCheck.kt : installs bundled providers; runs the pushed interop_plan.yaml into interop.yaml
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/JetpackCase.kt : base of a Jetpack-timed case: its rule, the counter check, the pin, the timed loop
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/JetpackConfig.kt : CaseSettings to MicrobenchmarkConfig; reportable metrics, CPU event counter argument check
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/PassArguments.kt : the run.passes pass and samples the host names, applied over a case's settings
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/PinnedCase.kt : one timed case under its cpu pin and energy setting
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/SampledAllocations.kt : allocation counting inside the timed phase for an allocation pass
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/Scope.kt : one scope's before and after calls and its interop check
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeCatalog.kt : loads the generated GeneratedScopes catalog
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeCheck.kt : calls both variants once and runs the interop check
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeInputs.kt : seeded bytes, text, files and secret keys for generated scopes
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeInteropFile.kt : writes scoped-interop.yaml
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeKeys.kt : key pairs for generated scopes: from the key planner once per run, kept on the device
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopedBenchmark.kt : parameterised Jetpack measurement per scope variant the host names
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopedInterop.kt : the scope check in its own process: every scope's verdict into scoped-interop.yaml, every call site's into callsite-verdicts.yaml
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopedPlan.kt : one process of the before/after run: bundled providers once, the run harness, the catalog's variants and the call sites
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/TraceWindowMarker.kt : WindowMarker over android.os.Trace sections
modules/android/src/main/AndroidManifest.xml : app manifest (allowBackup false)
modules/android/src/main/cpp/CMakeLists.txt : builds shared library affinity
modules/android/src/main/cpp/affinity.c : JNI sched_getaffinity and sched_setaffinity for cores 0..63
modules/android/src/main/kotlin/io/github/junekim0007/cryptobench/Affinity.kt : Kotlin binding for libaffinity.so
modules/android/src/main/res/values/strings.xml : app_name "crypto benchmark"
```
