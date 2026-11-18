package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.DefaultsDocument
import io.github.junekim0007.cryptobench.document.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

class DefaultsFileTest {

    private val committed = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "parity/defaults.yaml") }
        .firstOrNull { it.parentFile.isDirectory } ?: error("parity/ not found above ${File("").absoluteFile}")

    @Test
    fun parityDefaultsIsWhatThisBuildWrites() {
        val written = DefaultsDocument.HEADER + YamlCodec.DOCUMENT.dump(DefaultsDocument.of())
        if (System.getProperty("examples.update") != null) {
            committed.writeText(written)
            return
        }
        assertEquals("parity/defaults.yaml is not what this build writes; rerun with -Dexamples.update", written, committed.readText())
    }
}
