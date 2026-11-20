package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.guide.Guide
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.files.ContractsFolder
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.DuplicateKeyException
import org.yaml.snakeyaml.constructor.SafeConstructor
import java.io.File

/** tests/contracts/documents: preparation's example guide, as Python writes it, and config's example effective read through preparation's codec to the values their .json hold. */
class ContractsTest {

    private val guide = ContractsFolder.example("preparation", "guide.yaml")
    private val effective = ContractsFolder.example("config", "config_effective_example.yaml")

    private fun stated(name: String): Map<String, Any> = Yaml(SafeConstructor(LoaderOptions())).load(File(ContractsFolder.documents, "$name.json").readText())

    private fun read(file: File): Map<String, Any> = YamlCodec.DOCUMENT.load(file.readText())

    @Test
    fun theGuideAndEffectiveReadToTheirStatedValues() {
        assertEquals(stated("guide"), read(guide))
        assertEquals(stated("config_effective_example"), read(effective))
        Guide.read(guide)
        InboundFile.read(effective)
    }

    @Test
    fun currentBehaviourADuplicateKeyIsRefused() {
        assertThrows(DuplicateKeyException::class.java) { read(File(ContractsFolder.yamlCodec, "duplicate-key.yaml")) }
    }
}
