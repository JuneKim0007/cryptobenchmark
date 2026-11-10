package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/** parity/duplicate-key.yaml through discovery's codec, which also reads the config-owned effective.yaml in cli and androidTest. */
class ParityFixturesTest {

    private val parity = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "parity") }.firstOrNull { File(it, "duplicate-key.yaml").isFile }
        ?: error("parity/ not found above ${File("").absoluteFile}")

    @Test
    fun currentBehaviourADuplicateKeyKeepsTheLastValue() {
        // config and preparation refuse this file; C4 makes this codec refuse it too
        assertEquals(mapOf("schemaVersion" to 1, "run" to mapOf("seed" to 2), "seed" to "last"), YamlCodec().load(File(parity, "duplicate-key.yaml").readText()))
    }
}
