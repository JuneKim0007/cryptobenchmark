# Limits

| Limit | Measured |
|---|---|
| numbers are device-specific; the recorded run is an emulator, `cpuLocked: false`, one process | `measurements.json` `comparability` |
| cross-provider pairs, scope test set | 8 (type, algorithm) pairs, all RSA |
| cross-provider pairs, `all.yaml` | 10; key sizes fall back to provider defaults |
| AndroidKeyStore services that run | 0 of 12; keys must be created inside the keystore |
| phases measured | WARM only; `getInstance` + `init` per call is not timed |
| providers seen | those the device registers; a provider bundled in an app is `provider_not_on_device` |
| app scan | source files only; compiled dependencies are not scanned |
| default provider resolution | first by precedence; JCA delayed selection at `init` is not modelled |
| interchangeability | per capture: a `groups.json` belongs to the run directory built from one manifest |
