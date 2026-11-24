import io.github.junekim0007.cryptobench.contract.bundled.BundledProvider
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProviderException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class HostBundledTest {

    private val androidOnly = BundledProvider("g:android-only:1", "absent.AndroidProvider#newProvider", "Aliased")

    @Test
    fun anAndroidOnlyArtifactIsNotedNotInstalled() {
        val installed = HostBundled.install(listOf(androidOnly), setOf(androidOnly.artifact))
        assertEquals(emptyList<Any>(), installed.providers)
        assertEquals(listOf("bundled_android_only: g:android-only:1 (Aliased): its POM packaging is aar, which a host JVM cannot load; not installed"), installed.notes)
    }

    @Test
    fun anyOtherMissingClassIsStillRefused() {
        val refused = assertThrows(BundledProviderException::class.java) { HostBundled.install(listOf(androidOnly), emptySet()) }
        assertEquals("bundled_class_not_found", refused.code)
    }
}
