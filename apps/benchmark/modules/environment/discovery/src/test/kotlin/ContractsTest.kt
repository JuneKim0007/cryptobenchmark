package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.files.RepositoryFiles
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/** tests/contracts/yaml-codec/duplicate-key.yaml through discovery's codec, which also reads the config-owned effective.yaml in cli and androidTest. */
class ContractsTest {


    @Test
    fun currentBehaviourADuplicateKeyKeepsTheLastValue() {
        // config and preparation refuse this file; C4 makes this codec refuse it too
        assertEquals(mapOf("schemaVersion" to 1, "run" to mapOf("seed" to 2), "seed" to "last"), YamlCodec.CAPTURE.load(File(RepositoryFiles.yamlCodec, "duplicate-key.yaml").readText()))
    }
}
