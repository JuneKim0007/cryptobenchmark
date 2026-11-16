package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.document.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

/** variants per entry (override > include > run > default), the fallback and secure notices, and a written key source checked on the inventory. */
class PathsAndKeySourceTest {

    private val codec = YamlCodec.DOCUMENT
    private val inventory = InventoryBuilder().build(
        CaptureSource.parse(codec.load(Fixtures.CAPTURE)),
        TrialSource.parse(codec.load(Fixtures.TRIAL + GENERATORS)),
        InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"),
    )
    private val names = EffectiveBuilder.Files("global.yaml", "t.yaml", "inventory.yaml")

    private fun build(run: String, testSet: String) = EffectiveBuilder().build(
        GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: t.yaml}\n$run")),
        TestSetDocument.parse(codec.load("schemaVersion: 1\ndescription: d\n$testSet")), inventory, names)

    private fun variants(run: String, testSet: String) =
        build(run, testSet).providers.values.flatMap { types -> types.values.flatMap { it.entries } }.associate { it.key to it.value.variants }

    @Test
    fun anOverrideBeatsItsIncludeWhichBeatsTheRun() {
        val found = variants("run: {variants: [notFixed]}\n", """
            include:
            - {type: Cipher, name: AES/CBC/PKCS5PADDING, variants: [fixed]}
            - {type: Cipher, name: RSA}
            - {type: MessageDigest, name: SHA-256, variants: [fixed, notFixed]}
            overrides:
            - match: {type: MessageDigest}
              set: {variants: [notFixed]}
        """.trimIndent())
        assertEquals(mapOf("AES/CBC/PKCS5PADDING" to listOf("fixed"), "RSA" to listOf("notFixed"), "SHA-256" to listOf("notFixed")), found)
    }

    @Test
    fun theMoreSpecificIncludeWins() {
        val found = variants("", "include:\n- {type: Cipher, variants: [notFixed]}\n- {provider: SunJCE, type: Cipher, name: RSA, variants: [fixed]}\n- {type: Cipher, name: RSA}\n")
        assertEquals(listOf("fixed"), found.getValue("RSA"))
        assertEquals(listOf("notFixed"), found.getValue("AES/CBC/PKCS5PADDING"))
    }

    /** No run.variants: every path, secure noted once for the run and never written. */
    @Test
    fun theDefaultAsksEveryPathAndRunsTheBuiltOnes() {
        val effective = build("", "include:\n- {type: Cipher, name: RSA}\n- {type: MessageDigest}\n")
        assertEquals(listOf("fixed", "notFixed"), effective.run.variants)
        assertEquals(setOf(listOf("fixed", "notFixed")), effective.providers.values.flatMap { t -> t.values.flatMap { it.values } }.map { it.variants }.toSet())
        assertEquals(listOf("secure_path_unavailable: 2 entries ask for secure; the hardware-isolated key path is not built, so no secure case runs"),
            effective.warnings)
    }

    @Test
    fun onlySecureAskedIsASkipNotACase() {
        val effective = build("", "include:\n- {type: Cipher, name: RSA, variants: [secure]}\n- {type: MessageDigest}\n")
        assertEquals(listOf("secure_path_unavailable: only secure asked"), effective.skipped.map { it.reason })
        assertEquals(setOf("SUN"), effective.providers.keys)
    }

    @Test
    fun anInvalidValueFallsBackToFixedWithANotice() {
        val effective = build("run: {variants: [fast]}\n", "include:\n- {type: Cipher, name: RSA, variants: fixed}\n- {type: Cipher, name: AES/CBC/PKCS5PADDING}\n- {type: MessageDigest}\noverrides:\n- match: {type: MessageDigest}\n  set: {variants: [fixed, fixed]}\n- match: {name: AES/CBC/PKCS5PADDING}\n  set: {variants: []}\n")
        assertEquals(listOf("fixed"), effective.run.variants)
        assertEquals(setOf(listOf("fixed")), effective.providers.values.flatMap { t -> t.values.flatMap { it.values } }.map { it.variants }.toSet())
        assertEquals(listOf("run.variants [fast]", "include[0].variants fixed", "overrides[0].set.variants [fixed, fixed]", "overrides[1].set.variants []"),
            effective.warnings.map { it.removePrefix("variants_fallback: ").substringBefore(" is not") })
    }

    @Test
    fun theResolvedVariantsAreWrittenPerEntryAndReadBack() {
        val effective = build("", "include:\n- {type: Cipher, name: RSA, variants: [notFixed]}\n")
        val written = EffectiveDocument.of(effective)
        @Suppress("UNCHECKED_CAST")
        val entry = ((written["providers"] as Map<String, Map<String, Map<String, Map<String, Any>>>>).getValue("SunJCE").getValue("Cipher")).getValue("RSA")
        assertEquals(listOf("notFixed"), entry["variants"])
        assertEquals(effective.providers, EffectiveDocument.parse(codec.load(codec.dump(written))).providers)
    }

    @Test
    fun aWrittenKeySourceMustBeOnTheDevice() {
        val effective = build("", """
            include:
            - {type: Cipher, name: AES/CBC/PKCS5PADDING}
            - {type: Cipher, name: RSA}
            - {type: MessageDigest}
            overrides:
            - match: {name: AES/CBC/PKCS5PADDING}
              set: {key: {algorithm: aes, provider: same}}
            - match: {name: RSA}
              set: {key: {provider: SunRsaSign}}
            - match: {name: SHA-256}
              set: {key: {algorithm: HmacSHA256, provider: SUN}}
        """.trimIndent())
        assertEquals(listOf("SunJCE.Cipher.AES/CBC/PKCS5PADDING"), effective.providers.flatMap { (p, t) -> t.flatMap { (type, e) -> e.keys.map { "$p.$type.$it" } } })
        assertEquals(listOf(
            "no_key_generator: SUN registers no KeyGenerator or KeyPairGenerator HmacSHA256",
            "provider_not_installed: key.provider SunRsaSign, installed [SUN, SunJCE]",
        ), effective.skipped.map { it.reason })
    }

    @Test
    fun aKeySourceNameMustBeAString() {
        val failure = assertThrows(IllegalArgumentException::class.java) {
            TestSetDocument.parse(codec.load("schemaVersion: 1\ndescription: d\noverrides:\n- match: {name: RSA}\n  set: {key: {provider: 3}}\n"))
        }
        assertEquals("invalid: key {provider=3}, a name each", failure.message)
    }

    private companion object {
        val GENERATORS = """
            - provider: SunJCE
              type: KeyGenerator
              algorithm: AES
              instantiates: true
              defaultRun: {works: true, keyAlgorithm: AES, keyProvider: SunJCE, keySize: 256}
        """.trimIndent().prependIndent("") + "\n"
    }
}
