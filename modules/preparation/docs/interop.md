# interop

`InteropOracle.check(pair)`: whether two providers of one primitive interoperate. Code under `src/main/kotlin/interop/`; covered by `InteropOracleTest`.

## Check

| rule | value |
|---|---|
| member unavailable | both directions untested, `not_registered: ...`; mode `none` |
| mode `produce_consume` | the type has an artifact-consuming operation (DECRYPT, VERIFY) |
| mode `same_output` | otherwise |
| pair cases | seed 0; input size default 16 |
| untested `key_or_parameters_rejected` | `InvalidKeyException`, `InvalidAlgorithmParameterException`, `ClassCastException` |
| fail | `BadPaddingException`, `IllegalBlockSizeException`, `SignatureException`, `verify_failed` |
| verdicts | `compatible`, `incompatible`, `not_testable` |
| direction labels | `pass`, `fail`, `untested` |

## interop_plan.yaml

Schema `interop_plan` v1.

| key | rule |
|---|---|
| `pairs[]` | `{id, group, a, b, keySize?, inputSize?}`; ids unique |
| `a`, `b` | `{type, algorithm, provider}`; same type |

## interop.yaml

| key | holds |
|---|---|
| `schemaVersion` | `1` |
| `generatedFrom` | `plan`, `capture` |
| `verdicts[]` | `{id, verdict, mode, directions: {aToB, bToA}, reason}` |
