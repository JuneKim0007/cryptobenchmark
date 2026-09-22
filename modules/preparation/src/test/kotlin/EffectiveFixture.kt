package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.global.GlobalSettings
import io.github.junekim0007.cryptobench.preparation.global.OnFailure
import io.github.junekim0007.cryptobench.preparation.measurement.Metric
import io.github.junekim0007.cryptobench.preparation.measurement.Phase

object EffectiveFixture {

    val ONE_WARM_RUN = GlobalSettings(
        inputSizes = listOf(1024),
        phases = setOf(Phase.WARM),
        metrics = setOf(Metric.TIME),
        processRepetitions = 1,
        seed = 0L,
        onFailure = OnFailure.SKIP,
    )

    const val TEXT = """schemaVersion: 1
generatedFrom:
  global: global.yaml
  testSet: testsets/scope.yaml
  inventory: inventory.yaml
  capture: probe_20260921T204537Z.yaml
  trial: trial_20260921T204537Z.yaml
  device: {model: Pixel 9, manufacturer: Google, hardware: zuma, sdkInt: 37, release: '17', javaVersion: '0'}
run:
  inputSizes: [1024]
  phases: [WARM, COLD]
  metrics: [TIME]
  processRepetitions: 3
  seed: 0
policy: {onFailure: skip}
providers:
  SUN:
    MessageDigest:
      SHA-256: {}
  SunJCE:
    Cipher:
      AES/CBC/PKCS5PADDING:
        keySizes: [128, 256]
        operations: [DECRYPT]
        providerDefaults: [parameters]
      RSA:
        keySizes: [3072]
        inputSizes: [32]
        parameters: {class: javax.crypto.spec.OAEPParameterSpec, arguments: [SHA-256, MGF1, {field: java.security.spec.MGF1ParameterSpec.SHA256}, {field: javax.crypto.spec.PSource${'$'}PSpecified.DEFAULT}]}
        providerDefaults: [keySize, modeAndPadding]
skipped:
- {type: Mac, name: HmacSHA256, reason: 'no_match: nothing on this device matches the include'}
"""
}
