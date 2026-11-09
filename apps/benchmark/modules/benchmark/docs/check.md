# End-to-end check

The regression net for any change to preparation or the harness: every planned case goes the real path once, untimed, and its output is checked.

```
global.yaml + test set -> effective.yaml -> preparation -> PlanCheck -> Invocations.of(case) -> one harness call -> oracles -> check.yaml
```

| where | how one call is made | command |
|---|---|---|
| host JVM | `HostHarness.ONCE`, every case in one process | `pipeline.py --bench --check` (CLI main `CheckKt`) |
| device | `EndToEndCheck`: Jetpack `measureRepeated` under `androidx.benchmark.dryRunMode.enable=true`, every case in one process | `pipeline.py --device --check` |

The call's output goes to an `OutputHook`, which only check mode builds; the timed paths hand theirs to a BlackHole (`CheckModeTest`).

## Oracles, strongest first

| oracle | verdict from |
|---|---|
| `knownAnswer` | the case's own invocation over a vector's raw key, fixed parameters and input (`RawMaterial`), called the way the case is (`HostHarness.ONCE`, or a second dry-run `measureRepeated` on the device), output against the vector; vectors and their sources: `algorithms/vectors/` |
| `crossProvider` | every other provider the capture registers the service for checks the call's own output from the case's key, parameters and input: it decrypts the ciphertext, verifies the signature, recomputes a digest, MAC or agreed secret, or rebuilds a generated key pair. The key is rebuilt by the peer's own KeyFactory from its encoding, the parameters are read from the engine; what the peer cannot take is `not_checkable` (`peer_key_rejected`, `peer_parameters_rejected`, `parameters_not_recoverable`) |
| `contract` | per operation: length, the reverse recovers the input, tampering refused where a tag length was read back, verify true, a fresh key per call, a digest or MAC repeats its output when the call is replayed with the parameters it drew (a call that re-inits replays on a new instance) |
| `plan` | the steps one call made (from the invocation's `CallTrace`) equal what today's `perCall` plans, and the harness made exactly one call |
| `nonce` | encrypt that re-inits with a drawn per-init IV gives a new IV each call (read with `getIV`) |

Each verdict is `pass`, `fail` or `not_checkable` with a coded reason. A case passes, fails, errors (its call threw) or is `notRun` with preparation's or the plan check's reason.

## check.yaml

`schemaVersion: 1`; `generatedFrom` (harness, files, millis); `summary` (outcomes and verdict counts); `cases`: `id`, `outcome`, `case`, `plan` (`perCall`, `steps`), `observed` (`calls`, `steps`, `newInstance` (the engine held after the call is not the one before), `initsPerCall`, `iv` {by, bytes, distinctFromPreviousCall}, `key` {kind, provider, by same|foreign, class}), `oracles`, `outputDigest` (keyless cases whose second call gives the same bytes). Reasons drop object identity hashes (`Type@1a2b3c4d`); not-run cases sharing an id are numbered `#n` in the order of their fields, so a rerun names each the same.

## Baseline and diff

`CheckDiffKt <baseline check.yaml> <current check.yaml>` lists every case only in one file and every field that differs, and exits 1 on any. `generatedFrom` and `summary` are left out; no field holds a random value.
