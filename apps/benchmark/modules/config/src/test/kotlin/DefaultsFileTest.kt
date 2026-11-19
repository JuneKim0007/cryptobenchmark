package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.DefaultsDocument
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.files.ContractsFolder
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

class DefaultsFileTest {

    private val committed = File(ContractsFolder.defaults, "defaults.yaml")

    @Test
    fun committedDefaultsIsWhatThisBuildWrites() {
        val written = DefaultsDocument.HEADER + YamlCodec.DOCUMENT.dump(DefaultsDocument.of())
        if (System.getProperty("examples.update") != null) {
            committed.writeText(written)
            return
        }
        assertEquals("$committed is not what this build writes; rerun with -Dexamples.update", written, committed.readText())
    }
}
