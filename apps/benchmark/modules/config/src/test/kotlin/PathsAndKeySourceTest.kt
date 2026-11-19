package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.inventory.InventoryDocument
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
        GlobalDocument.parse(codec.load(Fixtures.seeded("schemaVersion: 1\nselection: {testSet: t.yaml}\n$run"))),
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
        assertEquals(mapOf("AES/CBC/PKCS5PADDING" to listOf("fixed"), "RSA" to emptyList(), "SHA-256" to listOf("notFixed")), found)
    }

    @Test
    fun theMoreSpecificIncludeWins() {
        val found = variants("", "include:\n- {type: Cipher, variants: [notFixed]}\n- {provider: SunJCE, type: Cipher, name: RSA, variants: [fixed]}\n- {type: Cipher, name: RSA}\n")
        assertEquals(listOf("fixed"), found.getValue("RSA"))
        assertEquals(listOf("notFixed"), found.getValue("AES/CBC/PKCS5PADDING"))
    }

    /** No run.variants: every path, secure noted once for the run and never written; an entry that asks nothing records nothing. */
    @Test
    fun theDefaultAsksEveryPathAndRunsTheBuiltOnes() {
        val effective = build("", "include:\n- {type: Cipher, name: RSA}\n- {type: MessageDigest}\n")
        assertEquals(listOf("fixed", "notFixed", "secure"), effective.run.variants)
        assertEquals(setOf(emptyList<String>()), effective.providers.values.flatMap { t -> t.values.flatMap { it.values } }.map { it.variants }.toSet())
        assertEquals(listOf("secure_path_unavailable: secure asked by 2 entries; the hardware-isolated key path runs KeyGenerator, KeyPairGenerator only"),
            effective.warnings)
    }

    /** Key generation keeps secure; a generator the trial cannot call runs secure alone; notFixed is noted once for the run. */
    @Test
    fun keyGenerationKeepsSecureAndNotesNotFixedOnce() {
        val effective = build("run: {variants: [fixed, notFixed, secure]}\n", "include:\n- {type: KeyGenerator}\n")
        assertEquals(mapOf("AES" to emptyList(), "SunTlsPrf" to listOf("secure")), variants("run: {variants: [fixed, notFixed, secure]}\n", "include:\n- {type: KeyGenerator}\n"))
        assertEquals(listOf("path_not_applicable: KeyGenerator (2 entries) applies [fixed, secure], [notFixed] dropped"), effective.warnings)
        assertEquals(emptyList<String>(), effective.skipped.map { it.reason })
    }

    @Test
    fun aGeneratorTheTrialCannotCallIsNotRunnableWithoutSecure() {
        val effective = build("run: {variants: [fixed]}\n", "include:\n- {type: KeyGenerator}\n- {type: KeyGenerator, name: SunTlsPrf, group: hw, variants: [secure]}\n")
        assertEquals(setOf("AES", "SunTlsPrf@hw"), effective.providers.getValue("SunJCE").getValue("KeyGenerator").keys)
        assertEquals(listOf("not_runnable: IllegalStateException: TlsPrfGenerator must be initialized"), effective.skipped.map { it.reason })
    }

    /** A written path the type's row does not apply leaves the entry; none left is a path_not_applicable skip, never a case. */
    @Test
    fun aWrittenPathTheRowDoesNotApplyIsDropped() {
        val effective = build("", "include:\n- {type: KeyGenerator, name: AES, variants: [fixed, notFixed]}\n- {type: KeyGenerator, name: AES, group: n, variants: [notFixed]}\n")
        assertEquals(listOf("fixed"), effective.providers.getValue("SunJCE").getValue("KeyGenerator").getValue("AES").variants)
        assertEquals(listOf("path_not_applicable: SunJCE.KeyGenerator.AES@n applies [fixed, secure], [notFixed] dropped"), effective.skipped.map { it.reason })
        assertEquals(listOf("path_not_applicable: KeyGenerator (1 entry) applies [fixed, secure], [notFixed] dropped"), effective.warnings)
    }

    @Test
    fun aBackingIsTeeOrStrongbox() {
        val effective = build("", "include:\n- {type: KeyGenerator, name: SunTlsPrf, variants: [secure]}\n- {type: KeyGenerator, name: AES}\n" +
            "overrides:\n- match: {name: SunTlsPrf}\n  set: {key: {backing: strongbox}}\n- match: {name: AES}\n  set: {key: {backing: glass}}\n")
        assertEquals(mapOf("backing" to "strongbox"), effective.providers.getValue("SunJCE").getValue("KeyGenerator").getValue("SunTlsPrf").key)
        assertEquals(listOf("invalid: key.backing glass, one of [tee, strongbox]"), effective.skipped.map { it.reason })
    }

    @Test
    fun onlySecureAskedIsASkipNotACase() {
        val effective = build("", "include:\n- {type: Cipher, name: RSA, variants: [secure]}\n- {type: MessageDigest}\n")
        assertEquals(listOf("secure_path_unavailable: secure asked by SunJCE.Cipher.RSA alone; the hardware-isolated key path runs KeyGenerator, KeyPairGenerator only"),
            effective.skipped.map { it.reason })
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

    /** A named key.provider in another case reaches effective.yaml in the inventory's spelling; same and any stay as written. */
    @Test
    fun aNamedKeyProviderIsWrittenInTheInventorysSpelling() {
        val effective = build("", """
            include:
            - {type: Cipher, name: AES/CBC/PKCS5PADDING}
            - {type: MessageDigest}
            overrides:
            - match: {name: AES/CBC/PKCS5PADDING}
              set: {key: {provider: sunjce}}
            - match: {name: SHA-256}
              set: {key: {algorithm: AES, provider: any}}
        """.trimIndent())
        assertEquals("SunJCE", effective.providers.getValue("SunJCE").getValue("Cipher").getValue("AES/CBC/PKCS5PADDING").key["provider"])
        assertEquals("any", effective.providers.getValue("SUN").getValue("MessageDigest").getValue("SHA-256").key["provider"])
    }

    /** `any`: the entry's own provider, then the inventory's order; refused only when no provider has the generator. */
    @Test
    fun anyTakesTheFirstProviderWithTheGenerator() {
        val effective = build("", """
            include:
            - {type: Cipher, name: AES/CBC/PKCS5PADDING}
            - {type: Cipher, name: RSA}
            - {type: MessageDigest}
            overrides:
            - match: {type: Cipher}
              set: {key: {provider: any}}
            - match: {name: SHA-256}
              set: {key: {algorithm: AES, provider: any}}
        """.trimIndent())
        assertEquals(listOf("SUN.MessageDigest.SHA-256", "SunJCE.Cipher.AES/CBC/PKCS5PADDING"),
            effective.providers.flatMap { (p, t) -> t.flatMap { (type, e) -> e.keys.map { "$p.$type.$it" } } })
        assertEquals(listOf("no_key_generator: no provider registers KeyGenerator or KeyPairGenerator RSA"), effective.skipped.map { it.reason })
    }

    /** key.algorithm may be any alias the capture lists for the generator, an OID too; inventory.yaml carries the aliases. */
    @Test
    fun aGeneratorAliasFromTheCaptureIsAccepted() {
        val capture = Fixtures.CAPTURE.replace("{name: SunJCE, version: '25', precedence: 2, services: []}",
            "{name: SunJCE, version: '25', precedence: 2, services: [{type: KeyGenerator, algorithm: AES, aliases: [2.16.840.1.101.3.4.1]}]}")
        val aliased = InventoryBuilder().build(CaptureSource.parse(codec.load(capture)), TrialSource.parse(codec.load(Fixtures.TRIAL + GENERATORS)),
            InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"))
        assertEquals(listOf("2.16.840.1.101.3.4.1"), aliased.providers.getValue("SunJCE").getValue("KeyGenerator").getValue("AES").aliases)
        assertEquals(aliased, InventoryDocument.parse(codec.load(codec.dump(InventoryDocument.of(aliased)))))
        val effective = EffectiveBuilder().build(
            GlobalDocument.parse(codec.load(Fixtures.seeded("schemaVersion: 1\nselection: {testSet: t.yaml}\n"))),
            TestSetDocument.parse(codec.load("schemaVersion: 1\ndescription: d\ninclude:\n- {type: Cipher}\noverrides:\n" +
                "- match: {name: AES/CBC/PKCS5PADDING}\n  set: {key: {algorithm: 2.16.840.1.101.3.4.1}}\n" +
                "- match: {name: RSA}\n  set: {key: {algorithm: 1.2.840.113549.1.1.1}}\n")), aliased, names)
        assertEquals(listOf("AES", "AES/CBC/PKCS5PADDING"), effective.providers.getValue("SunJCE").getValue("Cipher").keys.toList())
        assertEquals(listOf("no_key_generator: SunJCE registers no KeyGenerator or KeyPairGenerator 1.2.840.113549.1.1.1"), effective.skipped.map { it.reason })
    }

    /** A captured type without a setup-catalog row is a coded skip, never a case on a guessed path. */
    @Test
    fun aTypeWithoutACatalogueRowIsSkipped() {
        val capture = Fixtures.CAPTURE.replace("{name: SunJCE, version: '25', precedence: 2, services: []}",
            "{name: SunJCE, version: '25', precedence: 2, services: [{type: KEM, algorithm: DHKEM}]}")
        val trial = Fixtures.TRIAL + "- provider: SunJCE\n  type: KEM\n  algorithm: DHKEM\n  instantiates: true\n  defaultRun: {works: true}\n"
        val withKem = InventoryBuilder().build(CaptureSource.parse(codec.load(capture)), TrialSource.parse(codec.load(trial)), InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"))
        val effective = EffectiveBuilder().build(GlobalDocument.parse(codec.load(Fixtures.seeded("schemaVersion: 1\nselection: {testSet: t.yaml}\n"))),
            TestSetDocument.parse(codec.load("schemaVersion: 1\ndescription: d\ninclude:\n- {type: KEM}\n- {type: MessageDigest}\n")), withKem, names)
        assertEquals(setOf("SUN"), effective.providers.keys)
        assertEquals(listOf("not_in_catalogue: KEM has no row in setup-catalog.yaml"), effective.skipped.map { it.reason })
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
