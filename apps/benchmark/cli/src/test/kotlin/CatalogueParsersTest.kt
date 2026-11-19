import io.github.junekim0007.cryptobench.config.entry.EngineCatalog
import io.github.junekim0007.cryptobench.preparation.operation.SetupCatalog
import org.junit.Assert.assertEquals
import org.junit.Test

/** Config and preparation read the shipped setup-catalog.yaml through one EngineRows, each from its own resource. */
class CatalogueParsersTest {

    @Test
    fun theShippedCatalogueReadsTheSameInConfigAndPreparation() {
        for (type in listOf("MessageDigest", "Mac", "Signature", "KeyAgreement", "KeyGenerator", "KeyPairGenerator", "Cipher", "KEM")) {
            assertEquals(type, EngineCatalog.rows.applicable(type), SetupCatalog.standard.rows.applicable(type))
        }
        assertEquals(emptyList<String>(), SetupCatalog.standard.rows.applicable("KEM"))
        assertEquals(EngineCatalog.rows.generators, SetupCatalog.standard.rows.generators)
    }
}
