# <setup>

Placeholder.

Setup runs outside the benchmark: it checks what exists and loads what the run
needs, and never contributes to a measurement.

Source: `app/src/main/java/com/example/cryptobenchmark/setup/`

| Class | Does |
|---|---|
| `DeviceCryptoPrimitives` | enumerates `Security.getProviders()` and their services |
| `DevicePrimitiveRestrictions` | applies the include/exclude lists from `res/raw/restrictions.json` |
| `CryptoProvider`, `CryptoPrimitive`, `ConfigurableCryptoPrimitive` | provider and algorithm model |
| `CryptoParam`, `MultiCryptoParam` | algorithm parameter model |
| `PrimitiveStore` | provider-per-primitive map |
