package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.guide.Guide
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.DuplicateKeyException
import org.yaml.snakeyaml.constructor.SafeConstructor
import java.io.File

/** parity/: the guide Python writes and the effective file :config writes read through preparation's codec to the values their .json hold. */
class ParityFixturesTest {

    private val parity = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "parity") }.first { File(it, "duplicate-key.yaml").isFile }

    private fun stated(name: String): Map<String, Any> = Yaml(SafeConstructor(LoaderOptions())).load(File(parity, "$name.json").readText())

    private fun read(name: String): Map<String, Any> = YamlCodec().load(File(parity, "$name.yaml").readText())

    @Test
    fun theGuideAndEffectiveReadToTheirStatedValues() {
        assertEquals(stated("guide"), read("guide"))
        assertEquals(stated("effective"), read("effective"))
        Guide.read(File(parity, "guide.yaml"))
        InboundFile.read(File(parity, "effective.yaml"))
    }

    @Test
    fun currentBehaviourADuplicateKeyIsRefused() {
        assertThrows(DuplicateKeyException::class.java) { read("duplicate-key") }
    }
}
