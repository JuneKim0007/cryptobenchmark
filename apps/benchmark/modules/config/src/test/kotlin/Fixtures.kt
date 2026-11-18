package io.github.junekim0007.cryptobench.config

/** Environment's files as text, in the shape environment writes them; kept here so config builds and tests alone. */
object Fixtures {

    /** A global.yaml text with run.orderSeed, which every run names, added to its run section. */
    fun seeded(text: String): String = when {
        "orderSeed" in text -> text
        "run: {}" in text -> text.replace("run: {}", "run: {orderSeed: 1}")
        "run: {" in text -> text.replace("run: {", "run: {orderSeed: 1, ")
        Regex("(?m)^run:\\s*$").containsMatchIn(text) -> text.replaceFirst(Regex("(?m)^run:\\s*\n"), "run:\n  orderSeed: 1\n")
        else -> text + "run: {orderSeed: 1}\n"
    }

    const val CAPTURE = """
schemaVersion: 1
capturedAtMillis: 1700000000000
runtime: {model: Pixel 9, manufacturer: Google, hardware: zuma, sdkInt: 37, release: '17', javaVersion: '0'}
providers:
- {name: SunJCE, version: '25', precedence: 2, services: []}
- {name: SUN, version: '25', precedence: 1, services: []}
"""

    const val TRIAL = """
schemaVersion: 3
capturedAtMillis: 1700000000000
defaultRunInputSize: 1024
services:
- provider: SunJCE
  type: Cipher
  algorithm: AES
  instantiates: true
  defaultRun: {works: true, keyAlgorithm: AES, keyProvider: SunJCE, keySize: 256, inputSize: 1024, bareName: true}
  transformations:
  - name: AES/CBC/PKCS5PADDING
    instantiates: true
    defaultRun: {works: true, keyAlgorithm: AES, keyProvider: SunJCE, keySize: 256, inputSize: 1024, providerChose: AES iv=16B}
  - {name: AES/CTR/PKCS5PADDING, instantiates: false, error: 'NoSuchPaddingException: CTR mode must be used with NoPadding'}
- provider: SunJCE
  type: Cipher
  algorithm: RSA
  instantiates: true
  defaultRun: {works: true, keyAlgorithm: RSA, keyProvider: SunRsaSign, keySize: 3072, inputSize: 32, bareName: true}
- provider: SunJCE
  type: KeyGenerator
  algorithm: SunTlsPrf
  instantiates: true
  defaultRun: {works: false, error: 'IllegalStateException: TlsPrfGenerator must be initialized'}
- {provider: SunJCE, type: AlgorithmParameters, algorithm: AES, instantiates: true}
- provider: SUN
  type: MessageDigest
  algorithm: SHA-256
  instantiates: true
  defaultRun: {works: true, inputSize: 1024}
"""

    const val GLOBAL = """
schemaVersion: 1
selection:
  testSet: testsets/default_predefined.yaml
  exclude:
  - {type: KeyGenerator}
run: {inputSizes: [64, 1024], phases: [WARM], metrics: [TIME], variants: [fixed, notFixed], processRepetitions: 2, seed: 7, orderSeed: 20261115}
policy: {onFailure: skip}
"""

    const val TEST_SET = """
schemaVersion: 1
description: fixture scope
include:
- {type: Cipher, name: "AES*"}
- {type: Cipher, name: RSA}
- {type: KeyGenerator, name: SunTlsPrf}
- {type: MessageDigest, name: SHA-256}
- {type: Mac, name: HmacSHA256}
exclude:
- {name: AES}
overrides:
- match: {type: Cipher}
  set: {keySizes: [128], operations: [ENCRYPT]}
- match: {type: Cipher, name: "AES/*"}
  set: {keySizes: [128, 256]}
- match: {provider: SunJCE, type: Cipher, name: AES/CBC/PKCS5Padding}
  set: {parameters: {class: javax.crypto.spec.IvParameterSpec, arguments: [fresh(16)]}}
"""
}
