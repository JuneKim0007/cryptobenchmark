package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswerFile
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class KnownAnswerFileTest {

    private val vectors = KnownAnswerFile.read(CheckFixture.knownAnswers)

    @Test
    fun everyVectorCitesAnRfcOrNistSource() {
        assertTrue(vectors.isNotEmpty())
        vectors.forEach { assertTrue(it.id, it.source.startsWith("https://www.rfc-editor.org/") || "nist.gov/" in it.source) }
    }

    @Test
    fun aVectorMatchesByAnySpellingTheOperationAndTheKeyBits() {
        val wrap = vectors.first { "AESWrap" in it.algorithms && it.key.let { key -> key != null } && it.input.size == 16 }
        assertTrue(wrap.matches(BenchmarkCase("Cipher", "aes/kw/nopadding", "SunJCE", Operation.ENCRYPT, keySize = 128)))
        assertFalse(wrap.matches(BenchmarkCase("Cipher", "AESWrap", "SunJCE", Operation.ENCRYPT, keySize = 256)))
        assertFalse(wrap.matches(BenchmarkCase("Cipher", "AESWrap", "SunJCE", Operation.SIGN, keySize = 128)))
    }

    @Test
    fun hexInsideParametersBecomesBytesAndAnUnknownFieldIsRefused() {
        val gcm = vectors.first { "AES/GCM/NoPadding" in it.algorithms }
        assertEquals(12, ((gcm.parameters!!["arguments"] as List<*>)[1] as ByteArray).size)
        val failure = assertThrows(IllegalArgumentException::class.java) {
            KnownAnswerFile.parse(mapOf("vectors" to listOf(mapOf("id" to "x", "tag" to "y"))))
        }
        assertTrue(failure.message, failure.message!!.startsWith("unknown_keys: vectors[0] [tag]"))
    }
}
