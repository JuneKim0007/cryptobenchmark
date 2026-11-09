import io.github.junekim0007.cryptobench.preparation.guide.Guide
import io.github.junekim0007.cryptobench.preparation.request.Selection
import org.junit.Assert.assertEquals
import org.junit.Test

class GuideTest {

    private val gcm = mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128, "fresh(12)"))
    private val guide = Guide(mapOf(
        "P/Cipher/AES/GCM/NoPadding" to mapOf("parameters" to gcm, "keySizes" to listOf(128, 256)),
        "P/Cipher/Held" to mapOf("refused" to "key_inside_provider: this provider keeps its own keys"),
        "P/Cipher/Broken" to mapOf("problem" to "guide_recipe_unbuildable: nonce has no length"),
    ))

    private fun selection(algorithm: String, keySizes: List<Int> = emptyList(), parameters: Map<String, Any> = emptyMap()) =
        Selection("Cipher", algorithm, "P", keySizes = keySizes, parameters = parameters)

    @Test
    fun anItemTheGuideDoesNotHoldIsLoggedAndDropped() {
        val (ready, refused) = guide.joined(listOf(selection("Unknown")))
        assertEquals(emptyList<Selection>(), ready)
        assertEquals("not_in_guide: add an entry to measure it", refused.single().reason)
    }

    @Test
    fun anItemTheGuideDoesNotHoldIsDroppedEvenWithItsOwnParameters() {
        val (ready, refused) = guide.joined(listOf(selection("Unknown", parameters = mapOf("class" to "own"))))
        assertEquals(emptyList<Selection>(), ready)
        assertEquals("not_in_guide: add an entry to measure it", refused.single().reason)
    }

    @Test
    fun aRefusalHoldsEvenWithItsOwnParameters() =
        assertEquals("key_inside_provider: this provider keeps its own keys", guide.joined(listOf(selection("Held", parameters = mapOf("class" to "own")))).second.single().reason)

    @Test
    fun theGuideSaysHowAnItemIsBuilt() = assertEquals(gcm, guide.joined(listOf(selection("AES/GCM/NoPadding"))).first.single().parameters)

    @Test
    fun aKeySizeTheGuideDoesNotListIsRefusedAndTheRestRun() {
        val (ready, refused) = guide.joined(listOf(selection("AES/GCM/NoPadding", listOf(128, 192, 256))))
        assertEquals(listOf(128, 256), ready.single().keySizes)
        assertEquals("key_size_not_in_guide: [192], the guide lists [128, 256]", refused.single().reason)
    }

    @Test
    fun parametersSetForThisRunWin() {
        val own = mapOf("class" to "own")
        assertEquals(own, guide.joined(listOf(selection("AES/GCM/NoPadding", parameters = own))).first.single().parameters)
    }

    @Test
    fun aRecipeTheGuideCannotBuildIsRefused() =
        assertEquals("guide_recipe_unbuildable: nonce has no length", guide.joined(listOf(selection("Broken"))).second.single().reason)
}
