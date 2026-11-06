package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.bundled.AliasedProvider
import io.github.junekim0007.cryptobench.discovery.bundled.BundledInstaller
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProvider
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProviderException
import io.github.junekim0007.cryptobench.discovery.bundled.InstalledProvider
import io.github.junekim0007.cryptobench.discovery.bundled.ProviderFactory
import org.junit.After
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.MessageDigest
import java.security.Provider
import java.security.Security

class BundledInstallerTest {

    private val installer = BundledInstaller(ProviderFactory(javaClass.classLoader))

    private val before = Security.getProviders().map { it.name }

    @After
    fun removeInstalled() {
        Security.getProviders().map { it.name }.filterNot { it in before }.forEach(Security::removeProvider)
    }

    @Test
    fun aNoArgumentConstructorIsAppendedAfterEveryInstalledProvider() {
        val installed = installer.install(listOf(BundledProvider("test:fixture:1", FixtureProvider::class.java.name)))

        assertEquals(listOf(InstalledProvider(FixtureProvider.NAME, "test:fixture:1")), installed)
        assertEquals(before + FixtureProvider.NAME, Security.getProviders().map { it.name })
    }

    @Test
    fun aStaticFactoryCreatesTheProvider() {
        installer.install(listOf(BundledProvider("test:fixture:1", "${FixtureFactory::class.java.name}#newProvider")))

        assertEquals(FixtureProvider.NAME, Security.getProviders().last().name)
    }

    @Test
    fun aClashingNameWithoutAnAliasFailsWithACode() {
        val error = assertThrows(BundledProviderException::class.java) {
            installer.install(listOf(BundledProvider("test:clash:1", ClashingProvider::class.java.name)))
        }

        assertEquals("bundled_name_taken", error.code)
        assertEquals(before, Security.getProviders().map { it.name })
    }

    @Test
    fun aClashingNameIsRegisteredUnderItsAliasAndServesThroughIt() {
        val platform = Security.getProviders().toList()
        installer.install(listOf(BundledProvider("test:clash:1", ClashingProvider::class.java.name, "SUN-bundled")))

        val aliased = Security.getProvider("SUN-bundled")
        assertTrue(aliased is AliasedProvider)
        assertArrayEquals(platform.toTypedArray(), Security.getProviders().dropLast(1).toTypedArray())
        val digest = MessageDigest.getInstance("FIX", "SUN-bundled")
        assertEquals("SUN-bundled", digest.provider.name)
        assertArrayEquals(byteArrayOf(3), digest.digest(byteArrayOf(1, 2)))
        assertEquals(setOf("FIX"), aliased.services.map { it.algorithm }.toSet())
        assertTrue(aliased.services.all { it.provider === aliased })
        assertEquals("FIX", aliased.getProperty("Alg.Alias.MessageDigest.FIXED"))
    }

    @Test
    fun anAliasedLookupRebindsAServiceOnceAndKeepsItsAttributes() {
        installer.install(listOf(BundledProvider("test:clash:1", ClashingProvider::class.java.name, "SUN-bundled")))

        val aliased = Security.getProvider("SUN-bundled")
        val first = aliased.getService("MessageDigest", "FIX")
        assertSame(first, aliased.getService("MessageDigest", "fix"))
        assertSame(first, aliased.services.single { it.algorithm == "FIX" })
        assertEquals("yes", first?.getAttribute("Fixture"))
    }

    @Test
    fun aServiceListedBeforeItIsLookedUpStillInstantiates() {
        val aliased = AliasedProvider("Listed", ListingOthers())

        assertEquals(1, aliased.services.size)
        assertTrue(aliased.getService("MessageDigest", "FIX")!!.newInstance(null) is FixtureDigest)
    }

    @Test
    fun aTakenAliasFailsWithACode() {
        val error = assertThrows(BundledProviderException::class.java) {
            installer.install(listOf(BundledProvider("test:clash:1", ClashingProvider::class.java.name, before.first())))
        }

        assertEquals("bundled_alias_taken", error.code)
    }

    @Test
    fun reflectionFailuresNameTheirCause() {
        val cases = mapOf(
            "test.Missing" to "bundled_class_not_found",
            "java.lang.Object" to "bundled_not_a_provider",
            "${FixtureFactory::class.java.name}#absent" to "bundled_factory_not_found",
            "${FixtureFactory::class.java.name}#instanceMethod" to "bundled_factory_not_static",
            "${FixtureFactory::class.java.name}#failing" to "bundled_create_failed",
        )
        cases.forEach { (create, code) ->
            val error = assertThrows(create, BundledProviderException::class.java) {
                installer.install(listOf(BundledProvider("test:fixture:1", create)))
            }
            assertEquals(create, code, error.code)
        }
        assertEquals(before, Security.getProviders().map { it.name })
    }
}

class FixtureDigest : MessageDigest("FIX") {

    private var sum = 0

    override fun engineUpdate(input: Byte) {
        sum += input
    }

    override fun engineUpdate(input: ByteArray, offset: Int, len: Int) {
        for (index in offset until offset + len) sum += input[index]
    }

    override fun engineDigest(): ByteArray = byteArrayOf(sum.toByte()).also { sum = 0 }

    override fun engineReset() {
        sum = 0
    }
}

@Suppress("DEPRECATION")
open class FixtureProvider(name: String = NAME) : Provider(name, 1.0, "test fixture") {

    init {
        put("MessageDigest.FIX", FixtureDigest::class.java.name)
        put("Alg.Alias.MessageDigest.FIXED", "FIX")
        put("MessageDigest.FIX Fixture", "yes")
    }

    companion object {
        const val NAME = "BundledFixture"
    }
}

class ClashingProvider : FixtureProvider("SUN")

// As BC does: its listing's objects are not the ones getService returns, and newInstance refuses those.
class ListingOthers : FixtureProvider("ListingOthers") {
    private val looked = Service(this, "MessageDigest", "FIX", FixtureDigest::class.java.name, null, null)
    private val listed = Service(this, "MessageDigest", "FIX", FixtureDigest::class.java.name, null, null)

    override fun getService(type: String, algorithm: String): Service? = looked

    override fun getServices(): Set<Service> = setOf(listed)
}

class FixtureFactory {

    fun instanceMethod(): Provider = FixtureProvider()

    companion object {

        @JvmStatic
        fun newProvider(): Provider = FixtureProvider()

        @JvmStatic
        fun failing(): Provider = throw IllegalStateException("no native library")
    }
}
