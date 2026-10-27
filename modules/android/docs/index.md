# android

```
modules/android/.gitignore : ignores /build
modules/android/build.gradle : app module: SDK, NDK and CMake versions, androidx benchmark dependencies, release test build type
modules/android/docs/harness.md : instrumentation harness, device plan, core pinning
modules/android/docs/index.md : this map
modules/android/docs/scoped.md : scoped benchmark: generated scopes, interop check, before/after measurement
modules/android/proguard-rules.pro : Android Studio template, all rules commented out
modules/android/src/androidTest/java/.gitignore : ignores the generated scoped/ sources
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CorePin.kt : pins the measuring thread to one core and restores on close
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CorePins.kt : appends one line per pinned case to cpu-pins.yaml
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CovProbe.kt : fixed-ops-per-run timing experiment writing cov-probe.yaml
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CryptoBenchmark.kt : parameterised Jetpack measurement per timed case
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/DevicePlan.kt : prepares and checks the plan on the device from pushed files
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/DeviceProbe.kt : writes this device's capture and trial via discovery
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/EnergyDryBenchmark.kt : parameterised dry energy run per dry case
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/JetpackConfig.kt : CaseSettings to MicrobenchmarkConfig
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/PinnedCase.kt : one timed case under its cpu pin and energy setting
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/Scope.kt : one scope's before and after calls and its interop check
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeCatalog.kt : loads the generated GeneratedScopes catalog
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeCheck.kt : calls both variants once and runs the interop check
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeInputs.kt : seeded bytes, text and secret keys for generated scopes
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopeInteropFile.kt : writes scoped-interop.yaml
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/ScopedBenchmark.kt : parameterised Jetpack measurement per scope variant
modules/android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/TraceWindowMarker.kt : WindowMarker over android.os.Trace sections
modules/android/src/main/AndroidManifest.xml : app manifest (allowBackup false)
modules/android/src/main/cpp/CMakeLists.txt : builds shared library affinity
modules/android/src/main/cpp/affinity.c : JNI sched_getaffinity and sched_setaffinity for cores 0..63
modules/android/src/main/kotlin/io/github/junekim0007/cryptobench/Affinity.kt : Kotlin binding for libaffinity.so
modules/android/src/main/res/values/strings.xml : app_name "crypto benchmark"
```
