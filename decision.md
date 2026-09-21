# decisions

## Java to Kotlin for :environment:discovery

Problem: Java requires the folder path to match the package name, so every source file sat nine directories deep under an identical io/github/junekim0007/cryptobench prefix, and the folders said nothing about what was in them.
Mitigation: Kotlin for this module, which officially allows omitting the common root package folders.
Pro: nine path segments down to four, so the folders now show only adapter, contract, setting, write; data classes also removed the hand-written getters, null defaults and copying, taking the module from 1176 lines to 554; the capture it produces was diffed against the Java version and is identical.
Cons: a second language in the repository; the Kotlin standard library is added to the APK; measured code stays in Java until a control measurement shows Kotlin costs nothing in a timed loop.

## Modules instead of folders

Problem: crypto, discovery and benchmark were packages inside one app module, so layering was convention only.
Mitigation: four gradle modules, dependencies declared in the build.
Pro: a forbidden import is now a compile error, not a review comment; :environment:discovery compiles standalone on three JDKs in CI.
Cons: more build files; the Android build still cannot be run locally, so the wiring is unverified until #11.

## Gradle root at the repository root, modules under modules/

Problem: everything lived under android/, including a module with no Android dependency at all.
Mitigation: gradle root moved up; modules/ holds the four modules; settings.gradle maps each project directory.
Pro: the tree stops claiming discovery is Android code; root went from 21 entries to 15; task paths stay :android, not :modules:android.
Cons: every path in scripts, CI and docs had to move; two lines in benchmark.py are unverified until a real build.

## Package root io.github.junekim0007.cryptobench

Problem: com.example is a placeholder that Maven Central and the Play Store reject.
Mitigation: renamed across 62 files, one package per module.
Pro: publishable identity; one package per module reads as the module.
Cons: the app id changed, so an already-installed build must be uninstalled by hand.

## Packages named by role: adapter, contract, setting, write

Problem: probe/ said nothing inside a module whose whole job is probing, and PropertyKey.kt held both a parser and its result.
Mitigation: adapter reads the JCA, contract holds the model, setting reduces it, write writes it out; parser split from result.
Pro: each package names one responsibility; a reader can place a file without opening it.
Cons: the class is still called ProviderProbe while the package is adapter, so docs and issues use both words.

## The probe never calls Security itself

Problem: reading process-global state inside the probe would make it untestable off-device.
Mitigation: capture(providers) takes the provider array as a parameter.
Pro: the contract test drives it on Java 17, 21 and 25 with no device; hand-built providers can exercise malformed input.
Cons: something else has to supply the providers, and no production caller exists yet (#16).

## Two contracts: faithful capture, reduced setting

Problem: the benchmark needs 7 service types; a device offers 30, and names must round-trip exactly.
Mitigation: capture records everything as declared, original case; the converter crops to what the benchmark reads.
Pro: "why is my algorithm missing" is answerable from the capture; the setting stays benchmark-sized.
Cons: two shapes for the same data; every new field is added in two places.

## Service type stays a String, benchmark scope stays an enum

Problem: an enum over JCA service types would need editing whenever a JDK adds one.
Mitigation: types are strings in the capture; only our own 7-type scope is a closed set.
Pro: KDF and KEM appeared in recent JDKs and cost nothing; unknown attributes are kept as strings rather than dropped.
Cons: typos in a type name are not caught by the compiler.

## Flattened transformation strings, failure by exception

Problem: 458 declared transformations expand from 59 registered services, and 24 of them do not work; nothing in the property map says which.
Mitigation: pass one transformation string to getInstance and let it throw.
Pro: no reimplementation of provider logic we cannot see; getInstance is the only authority.
Cons: an unsupported case is only discovered at run time, so the failure must be recorded as a result rather than left as a missing row.

## Grouping by "is the prefix itself registered"

Problem: splitting a name at the first slash mis-groups PBEWithHmacSHA512/224AndAES_128, whose slash is inside a digest name.
Mitigation: split only when the prefix is a registered algorithm of the same type in that provider; otherwise keep the whole name.
Pro: no list to maintain; a new provider groups correctly the day it ships.
Cons: worse grouping — AES_128/CBC/NoPadding and its 23 siblings become groups of one; an unidentified bucket or a user override would be needed for analysis.

## Discovery reports, never configures

Problem: config reading inside discovery would couple it to files and formats and break desktop testability.
Mitigation: scope and output target are constructor parameters; no file reading in the module.
Pro: runs on a plain JVM with one compileOnly dependency; the weekly CI check is possible because of it.
Cons: every caller must supply what it wants, and no caller exists yet.

## One build, logical modules only

Problem: modular structure invites per-module versioning and publishing.
Mitigation: modules are a compile-time boundary; no maven-publish, no per-module versions.
Pro: no packaging machinery to maintain for a single-artifact project.
Cons: :environment:discovery is portable in principle but produces no consumable artifact; tools/jca-contract reaches into its source directory instead of depending on it.

## tools/jca-contract as a temporary second build

Problem: AGP 3.0 and Gradle 6.5 cannot run on a modern JDK, so discovery could not be compiled or tested on Java 17, 21 or 25.
Mitigation: a small standalone Gradle project pointing at the same sources, with a pinned wrapper.
Pro: the JCA contract check and the playground run today instead of after #11.
Cons: a second build file duplicates the Kotlin, JUnit and org.json versions, and they have already drifted once.
