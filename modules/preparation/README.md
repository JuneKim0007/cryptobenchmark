# Preparation

> An independent module that turns one `effective.yaml` into cases the harness can measure, before any timer starts.

## Responsibilities

- Read `effective.yaml` in order: the file, then the global settings, then the primitives.
- Read the capture and trial for what the device serves, and reject what it cannot run by name.
- Build each case's key, input and parameters, and call every case once to prove it runs.
- Hand the harness that same call: `Invocations.of(prepared)` is what the timer wraps.
- Write `prepared.yaml`: every case as built, for reading and for the harness to check itself against.

  1. For more information, refer to <prepare.md>.

## Files

Every class and its role: the Classes table in [docs/prepare.md](docs/prepare.md). Examples are in `example/`, tests in `src/test/kotlin/`.

## Limitations

- Reads YAML only: `effective.yaml`, the capture and the trial. It never probes the device itself.
- A case is proved by one call, not by a measurement: timing, warmup and iteration counts belong to the harness.
- `TYPE_DEFAULT` cases are not called: nothing here knows how to invoke an engine type it has no rule for.

## Example

`example/` is one small device: capture, trial and effective in; prepared and skipped out.
`ExampleFilesTest` prepares every case against the running JVM and compares both outputs with the committed files.
Regenerate them with `./gradlew :preparation:test -Dexamples.update`.
