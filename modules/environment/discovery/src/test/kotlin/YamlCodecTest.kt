package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Test
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class YamlCodecTest {

    private val codec = YamlCodec()

    private val document = linkedMapOf(
        "name" to "SunJCE",
        "version" to "25",
        "services" to listOf(linkedMapOf("type" to "Cipher", "aliases" to listOf("a", "b"))),
    )

    @Test
    fun dumpsBlockStyleAndQuotesNumberLikeStrings() {
        assertEquals(
            "name: SunJCE\nversion: '25'\nservices:\n- type: Cipher\n  aliases:\n  - a\n  - b\n",
            codec.dump(document),
        )
    }

    @Test
    fun loadsWhatItDumped() {
        assertEquals(document, codec.load(codec.dump(document)))
    }

    /** snakeyaml's Yaml is not thread-safe; the codec builds one per call so a shared codec is. */
    @Test
    fun oneCodecServesManyThreads() {
        val expected = codec.dump(document)
        val pool = Executors.newFixedThreadPool(8)
        val results = (1..400).map { pool.submit<String> { codec.dump(document) } }
        pool.shutdown()
        pool.awaitTermination(30, TimeUnit.SECONDS)
        results.forEach { assertEquals(expected, it.get()) }
    }
}
