# native budget

A forced GC and finalization every K timed calls, outside the timer, and what it cost on each row. Where it sits in a sample: [measure.md](measure.md#what-one-sample-is).

Why: some providers keep native memory per call that only a finalizer frees (Conscrypt's `HMAC_CTX`, made on every init, inside `doFinal` and on reset). An app calls slowly enough for the one `FinalizerDaemon` to keep up; a benchmark calls as fast as it can, the backlog grows until the process aborts (`std::bad_alloc`, issue #84). A forced GC and `runFinalization` returns that memory, so it is a backlog only the benchmark creates, not a leak.

| rule | value |
|---|---|
| when | after every 50 000th timed call (`NativeBudget.CALLS`: about 55 MB of contexts at about 1.1 KB each), counted over the warm-up and the samples |
| what | `System.gc()` then `System.runFinalization()`, every engine type, host and device |
| timing | outside every sample: host `HostHarness` subtracts the paused time from the sample and `TimedLoop` from its window; device `JetpackCase` runs it inside `runWithMeasurementDisabled` |
| in the timed loop | one counter increment and compare per call |
| reported | `nativeCleanup: {everyCalls, cleanups, pausedNanos}` on each case's row; merged processes add `cleanups` and `pausedNanos` ([results.md](../../../../../docs/results.md#benchmarkjson-case-fields)) |
| device | `NativeCleanups` appends `"<id>": {everyCalls, cleanups, pausedNanos}` to `native-cleanup.yaml`; the runner pulls it and `ConvertKt --cleanup=` joins it by case id |
| not covered | energy windows (`CaseRuns`) and the check's one call |
