package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Test

class YamlCodecTest {

    private val codec = YamlCodec()

    private val document = linkedMapOf(
        "name" to "SunJCE",
        "version" to "25",
        "services" to listOf(linkedMapOf("type" to "Cipher", "aliases" to listOf("a", "b"))),
    )

    @Test
    fun dumpsBlockStyleQuotesNumberLikeStringsAndLoadsItBack() {
        val text = codec.dump(document)
        assertEquals("name: SunJCE\nversion: '25'\nservices:\n- type: Cipher\n  aliases:\n  - a\n  - b\n", text)
        assertEquals(document, codec.load(text))
    }
}
