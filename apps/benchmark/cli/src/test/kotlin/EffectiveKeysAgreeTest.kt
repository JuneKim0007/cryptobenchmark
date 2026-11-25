import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.settings.RunKeys
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import io.github.junekim0007.cryptobench.preparation.request.PrimitiveReader
import org.junit.Assert.assertEquals
import org.junit.Test

/** Preparation copies :config's effective.yaml keys: every key config writes, each optional one set here, must read without unknown_keys. */
class EffectiveKeysAgreeTest {

    @Test
    fun everyKeyConfigWritesIsOnePreparationKnows() {
        val codec = YamlCodec.DOCUMENT
        val written = codec.dump(linkedMapOf<String, Any>("schemaVersion" to EffectiveDocument.schemaVersion) + EffectiveDocument.of(EffectiveDocument.parse(codec.load(EVERY_KEY))))
        val inbound = InboundFile.read("effective.yaml", written)
        GlobalReader.read(inbound)
        PrimitiveReader.read(inbound)
        val entry = (((inbound.providers.getValue("SunJCE") as Map<*, *>)["Cipher"] as Map<*, *>)["AES/GCM/NoPadding"] as Map<*, *>).keys
        assertEquals(listOf(TOP, RUN, ENTRY), listOf(codec.load(written).keys, inbound.run.keys, entry))
    }

    private companion object {
        // Every optional key set, so config writes each one.
        val EVERY_KEY = """
            generatedFrom:
              global: g.yaml
              testSet: t.yaml
              inventory: inventory.yaml
              capture: probe_20261108T000000Z.yaml
              trial: t.yaml
              device: {model: m, manufacturer: m, hardware: h, sdkInt: 0, release: r, javaVersion: '17', defaultKeySizeProperty: '', fingerprint: f, javaVendor: v, javaRuntimeVersion: '17', osName: o, osArch: a}
              layers: [{path: g.yaml, sha256: '00'}]
              settings: {run.seed: layer 1 g.yaml}
            run:
              inputSizes: [64]
              phases: [WARM]
              metrics: [TIME]
              variants: [fixed]
              processRepetitions: 1
              seed: 0
              orderSeed: 7
              passes: {timing: {samples: 5, thermalGate: {pollSeconds: 20}, caseCooldownSeconds: 3}}
              thermalThrottleSleepSeconds: 1
              caseCooldownSeconds: 1
              warmup: {iterations: 1, jobs: []}
              thermalGate: {temperatureKeptCelsius: 36.0}
              harness: {iterations: 2}
            policy: {onFailure: skip}
            analysis: {charts: [latency]}
            bundledProviders: [{artifact: 'org.example:p:1', create: org.example.P, alias: Example}]
            providers:
              SunJCE:
                Cipher:
                  AES/GCM/NoPadding:
                    keySizes: [128]
                    inputSizes: [64]
                    key: {algorithm: AES, provider: same}
                    parameters: {class: javax.crypto.spec.GCMParameterSpec, arguments: [128, fresh(12)]}
                    operations: [ENCRYPT]
                    variants: [fixed]
                    providerDefaults: [keySize]
                    harness: {iterations: 2}
                    from: {testSet: t.yaml, includes: [{index: 0, type: Cipher, name: AES/GCM/NoPadding}]}
        """.trimIndent()

        // What config writes; warnings and skipped go to report.yaml.
        val TOP = setOf("schemaVersion", "generatedFrom", "runId", "run", "policy", "analysis", "bundledProviders", "providers")
        val RUN = RunKeys.ALL.toSet()
        val ENTRY = setOf("keySizes", "inputSizes", "key", "parameters", "operations", "variants", "providerDefaults", "harness", "from")
    }
}
