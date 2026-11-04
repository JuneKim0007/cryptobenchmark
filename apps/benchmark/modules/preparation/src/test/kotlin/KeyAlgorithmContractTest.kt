package io.github.junekim0007.cryptobench.preparation.key.plan

import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class KeyAlgorithmContractTest {

    private val keyed = setOf("Cipher", "Signature", "Mac", "KeyAgreement")

    private val trial: File =
        System.getProperty("trial")?.let(::File) ?: File("example", "preparation_trial_example.yaml")

    @Test
    fun derivationOffersWhateverKeyAlgorithmTheDeviceMeasured() {
        val measured = measurements()
        assertTrue("no measured keyAlgorithm in $trial, so this proves nothing", measured.isNotEmpty())

        val disagreed = measured.filter { (type, algorithm, keyAlgorithm) ->
            KeyAlgorithmName.candidates(type, algorithm).none { it.algorithm == keyAlgorithm }
        }

        assertEquals(
            "derivation does not offer what the device measured, ${disagreed.size} of ${measured.size} measurements in $trial",
            emptyList<String>(),
            disagreed.map { (type, algorithm, keyAlgorithm) ->
                "$type $algorithm: device $keyAlgorithm, derived ${KeyAlgorithmName.candidates(type, algorithm).map { it.algorithm }}"
            },
        )
    }

    private fun measurements(): List<Triple<String, String, String>> {
        val services = list(YamlCodec().load(trial.readText())["services"])
        val measured = mutableListOf<Triple<String, String, String>>()
        for (service in services) {
            val type = service["type"]?.toString() ?: continue
            if (type !in keyed) continue
            val algorithm = service["algorithm"]?.toString() ?: continue
            keyAlgorithmOf(service["defaultRun"])?.let { measured += Triple(type, algorithm, it) }
            for (transformation in list(service["transformations"])) {
                val name = transformation["name"]?.toString() ?: continue
                keyAlgorithmOf(transformation["defaultRun"])?.let { measured += Triple(type, name, it) }
            }
        }
        return measured
    }

    private fun keyAlgorithmOf(defaultRun: Any?): String? =
        section(defaultRun)["keyAlgorithm"]?.toString()?.takeIf { it.isNotBlank() }

    @Suppress("UNCHECKED_CAST")
    private fun list(value: Any?): List<Map<String, Any>> = value as? List<Map<String, Any>> ?: emptyList()

    @Suppress("UNCHECKED_CAST")
    private fun section(value: Any?): Map<String, Any> = value as? Map<String, Any> ?: emptyMap()
}
