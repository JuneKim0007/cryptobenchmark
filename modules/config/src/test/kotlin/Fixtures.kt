package io.github.junekim0007.cryptobench.config

/** Environment's files as text, in the shape environment writes them; kept here so config builds and tests alone. */
object Fixtures {

    const val CAPTURE = """
schemaVersion: 1
capturedAtMillis: 1700000000000
runtime: {model: Pixel 9, manufacturer: Google, hardware: zuma, sdkInt: 37, release: '17', javaVersion: '0'}
providers:
- {name: SunJCE, version: '25', precedence: 2, info: x, usable: true, services: []}
- {name: SUN, version: '25', precedence: 1, info: x, usable: true, services: []}
"""

    const val TRIAL = """
schemaVersion: 2
capturedAtMillis: 1700000000000
services:
- provider: SunJCE
  type: Cipher
  algorithm: AES
  instantiates: true
  defaultRun: {works: true, keyAlgorithm: AES, keyProvider: SunJCE, keySize: 256, inputSize: 1024, bareName: true}
  transformations:
  - {name: AES, instantiates: true}
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
  testSet: testsets/scope.yaml
  exclude:
  - {type: KeyGenerator}
run: {inputSizes: [64, 1024], phases: [WARM], metrics: [TIME], processRepetitions: 2, seed: 7}
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
  set: {keySizes: [128]}
- match: {type: Cipher, name: "AES/*"}
  set: {keySizes: [128, 256]}
- match: {provider: SunJCE, type: Cipher, name: AES/CBC/PKCS5Padding}
  set: {parameters: {class: javax.crypto.spec.IvParameterSpec, arguments: [fresh(16)]}}
"""
}
