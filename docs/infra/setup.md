# <setup>

Placeholder.

User config and user-supplied inputs for a run. Never contributes to a measurement.

Source: `android/app/src/main/java/io/github/junekim0007/cryptobench/setup/`

| Class | Does |
|---|---|
| `config/Config` | reads run parameters from `/sdcard/CryptoBenchmark.config` |

Device capability is not setup — it lives in module `:discovery`, see `probe.md` there.
