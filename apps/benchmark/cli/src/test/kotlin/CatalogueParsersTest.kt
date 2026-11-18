import io.github.junekim0007.cryptobench.config.entry.EnginePaths
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.preparation.operation.SetupCatalog
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

/** Characterization: config EnginePaths and preparation SetupCatalog read one setup-catalog document; where they differ today is pinned. */
class CatalogueParsersTest {

    private val document = YamlCodec.DOCUMENT.load(
        """
        schemaVersion: 1
        engines:
          Mac: {fixed: operation}
          KeyGenerator: {variants: [fixed, secure], generates: secretKey}
          Signature: {fixed: operation, variants: [fixed, fixed]}
          KeyPairGenerator: {variants: [fixed, secure], generates: keyPair}
          KeyAgreement: {fixed: operation, generates: keyPair}
        """.trimIndent(),
    )
    private val config = EnginePaths(document)
    private val preparation = SetupCatalog(document)

    @Test
    fun todayATypeWithoutARowAppliesNothingInConfigButFixedAndSecureInPreparation() {
        assertEquals(emptyList<String>(), config.applicable("KEM"))
        assertEquals(listOf("fixed", "secure"), preparation.applicable("KEM"))
    }

    @Test
    fun aRowWithoutVariantsAndAValidRowAgree() {
        for ((type, paths) in listOf("Mac" to listOf("fixed", "notFixed"), "mac" to listOf("fixed", "notFixed"), "KeyGenerator" to listOf("fixed", "secure"))) {
            assertEquals(type, paths, config.applicable(type))
            assertEquals(type, paths, preparation.applicable(type))
        }
    }

    @Test
    fun todayInvalidVariantsAreRefusedByBothWithDifferentText() {
        val byConfig = assertThrows(IllegalArgumentException::class.java) { config.applicable("Signature") }.message
        val byPreparation = assertThrows(IllegalArgumentException::class.java) { preparation.applicable("Signature") }.message
        assertEquals("invalid: /setup-catalog.yaml engines.Signature.variants [fixed, fixed], distinct names of [fixed, notFixed, secure]", byConfig)
        assertEquals("invalid: setup-catalog.yaml engines.Signature.variants [fixed, fixed], distinct names of [fixed, notFixed, secure]", byPreparation)
    }

    @Test
    fun todayADuplicateGeneratorIsListedByConfigAndRefusedByPreparation() {
        assertEquals(listOf("KeyGenerator", "KeyPairGenerator", "KeyAgreement"), config.generators)
        assertEquals("KeyGenerator", preparation.generator(SetupCatalog.SECRET_KEY))
        val refused = assertThrows(IllegalArgumentException::class.java) { preparation.generator(SetupCatalog.KEY_PAIR) }
        assertEquals("invalid: setup-catalog.yaml engines name [KeyPairGenerator, KeyAgreement] with generates: keyPair, exactly one wanted", refused.message)
    }

    @Test
    fun theShippedCatalogueReadsTheSameInBothButForAMissingType() {
        for (type in listOf("MessageDigest", "Mac", "Signature", "KeyAgreement", "KeyGenerator", "KeyPairGenerator", "Cipher")) {
            assertEquals(type, EnginePaths.catalog.applicable(type), SetupCatalog.standard.applicable(type))
        }
        assertEquals(emptyList<String>(), EnginePaths.catalog.applicable("KEM"))
        assertEquals(listOf("fixed", "secure"), SetupCatalog.standard.applicable("KEM"))
    }
}
