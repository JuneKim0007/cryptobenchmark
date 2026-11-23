package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.catalogue.Recipes
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotSame
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.Security
import java.security.interfaces.ECPublicKey
import java.security.spec.ECGenParameterSpec

/** An entry's keyGeneration row made by Recipes and bound by ParameterBinder at a build; each recipe it cannot make or bind is a refusal with its code; DefaultKeys keeps one pair per spec. */
class KeyGenerationSpecTest {

    private val recipes = Recipes.parse(
        """
        schemaVersion: 1
        recipes:
          r.curve: {class: java.security.spec.ECGenParameterSpec, args: [{role: curve, kind: string}]}
          r.group: {builder: namedGroupSpec}
          r.pair: {class: java.security.spec.ECGenParameterSpec, args: [{role: curve, kind: string}, {role: other, kind: string}]}
          r.absent: {class: no.such.Spec, args: [{role: curve, kind: string}]}
        """.trimIndent(),
    )

    private fun entry(vararg rows: String) = FamilyCatalogue.parse(listOf(
        "family: f\nalgorithms:\n  Signature|S:\n    required:\n" + rows.joinToString("") { "    - $it\n" },
    )).entries.single()

    private fun refusal(vararg rows: String) = (KeyGenerationSpec.of(entry(*rows), null, recipes) as KeyGenerationSpec.Refused).reason

    @Test
    fun aClassRecipeOfTheRowsValueIsBuiltAndBound() {
        val built = KeyGenerationSpec.of(entry("{name: curve, recipe: r.curve, value: secp256r1, passedTo: keyGeneration}"), null, recipes) as KeyGenerationSpec.Built
        assertEquals("r.curve[secp256r1]", built.label)
        assertEquals("secp256r1", (built.spec as ECGenParameterSpec).name)
        assertSame(KeyGenerationSpec.None, KeyGenerationSpec.of(entry("{name: curve, recipe: r.curve, value: x, passedTo: init}"), null, recipes))
    }

    @Test
    fun eachUnbuildableRowIsRefusedWithItsCode() {
        assertTrue(refusal("{name: group, recipe: r.group, value: ffdhe2048, passedTo: keyGeneration}").startsWith("${Recipes.CODE}: r.group is not a constructor"))
        assertTrue(refusal("{name: curve, recipe: r.pair, value: secp256r1, passedTo: keyGeneration}").startsWith("${Recipes.CODE}: other has no value"))
        assertTrue(refusal("{name: shape, recipe: r.curve, value: secp256r1, passedTo: keyGeneration}").startsWith("${Recipes.CODE}: curve has no value"))
        assertTrue(refusal("{name: curve, recipe: r.absent, value: secp256r1, passedTo: keyGeneration}").startsWith("bind_failed: keyGeneration.r.absent: no class no.such.Spec"))
        val several = KeyGenerationSpec.of(entry("{name: curve, recipe: r.curve, value: a, passedTo: keyGeneration}", "{name: group, recipe: r.group, value: b, passedTo: keyGeneration}"), null, recipes) as KeyGenerationSpec.Refused
        assertEquals("${Recipes.CODE}: [r.curve, r.group] are several objects for one keyGeneration", several.reason)
        assertEquals("r.curve, r.group", several.recipe)
    }

    @Test
    fun aDeviationsRowAppliesOnlyAtItsBuilds() {
        val catalogue = FamilyCatalogue.bundled(FamilyCatalogue.KEYED + FamilyCatalogue.GENERATORS)
        val ecnr = catalogue.of("Signature", "SHA256WITHECNR")!!
        assertEquals("jca.ecGenSpec[secp521r1]", (KeyGenerationSpec.of(ecnr, catalogue.build("BundledBC", "jdk-25")) as KeyGenerationSpec.Built).label)
        assertSame(KeyGenerationSpec.None, KeyGenerationSpec.of(ecnr, catalogue.build("SunEC", "jdk-25")))
    }

    @Test
    fun defaultKeysCachesOnePairPerSpec() {
        val sun = Security.getProvider("SunEC")
        val keys = DefaultKeys(listOf(sun), KeyCandidates(FamilyCatalogue(emptyList()), null, emptyList()))
        fun spec(curve: String) = KeyGenerationSpec.Built("c[$curve]", ECGenParameterSpec(curve))
        val p256 = keys.pairFrom(sun, "EC", null, spec("secp256r1")).getOrThrow()
        val p384 = keys.pairFrom(sun, "EC", null, spec("secp384r1")).getOrThrow()
        assertNotSame(p256, p384)
        assertEquals(listOf(256, 384), listOf(p256, p384).map { (it.keys.public as ECPublicKey).params.curve.field.fieldSize })
        assertSame(p256, keys.pairFrom(sun, "EC", null, spec("secp256r1")).getOrThrow())
        assertNotSame(p256, keys.pairFrom(sun, "EC", null).getOrThrow())
    }
}
