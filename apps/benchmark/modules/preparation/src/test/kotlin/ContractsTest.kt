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

/** contracts/documents: the guide Python writes and the effective file :config writes read through preparation's codec to the values their .json hold. */
class ContractsTest {


    private fun stated(name: String): Map<String, Any> = Yaml(SafeConstructor(LoaderOptions())).load(File(ContractsFolder.documents, "$name.json").readText())

    private fun read(folder: File, name: String): Map<String, Any> = YamlCodec.DOCUMENT.load(File(folder, "$name.yaml").readText())

    @Test
    fun theGuideAndEffectiveReadToTheirStatedValues() {
        assertEquals(stated("guide"), read(ContractsFolder.documents, "guide"))
        assertEquals(stated("effective"), read(ContractsFolder.documents, "effective"))
        Guide.read(File(ContractsFolder.documents, "guide.yaml"))
        InboundFile.read(File(ContractsFolder.documents, "effective.yaml"))
    }

    @Test
    fun currentBehaviourADuplicateKeyIsRefused() {
        assertThrows(DuplicateKeyException::class.java) { read(ContractsFolder.yamlCodec, "duplicate-key") }
    }
}
