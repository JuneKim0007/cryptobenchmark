package io.github.junekim0007.cryptobench.document

import io.github.junekim0007.cryptobench.document.catalogue.CatalogueOverlays
import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.catalogue.GroupExemplars
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/** One build's view of an entry: behaviours where the entry has the parent, deviations in order, the entry's own providers section last; a build by platform. */
class FamilyCatalogueTest {

    private val builds = """
        schemaVersion: 1
        builds:
          "P @ android-30": {name: P}
          "P @ android-33": {name: P}
          "B @ some:artifact:1": {name: B}
        providers:
          P:
            behaviour: {key.origin: provider, absent.field: x}
            registers:
            - {builds: [P @ android-33], names: [T|A]}
    """.trimIndent()

    private val deviations = """
        schemaVersion: 1
        deviations:
          first:
            builds: [P]
            names: [t|a]
            set: {key.type: X, required.iv: null}
          second:
            builds: [P @ android-33]
            names: [T|A]
            set: {key.type: Y}
    """.trimIndent()

    private val family = """
        schemaVersion: 1
        family: f.none
        algorithms:
          T|A:
            key: {type: K, origin: app}
            required:
            - {name: iv, bytes: 16}
            - {name: input}
            providers:
              P @ android-30: {key.origin: own}
          T|Plain:
            key: {type: K}
    """.trimIndent()

    private val catalogue = FamilyCatalogue.parse(listOf(family), CatalogueOverlays.parse(builds, deviations))

    @Test
    fun eachBuildSeesItsOwnView() {
        val entry = catalogue.of("t", "a")!!
        assertEquals("f.none", entry.family)
        assertEquals(mapOf("type" to "K", "origin" to "app"), entry.section("key"))
        assertEquals(mapOf("type" to "X", "origin" to "own"), entry.section("key", "P @ android-30"))
        assertEquals(mapOf("type" to "Y", "origin" to "provider"), entry.section("key", "P @ android-33"))
        assertEquals(listOf(mapOf("name" to "input")), entry.fields("P @ android-33")["required"])
        assertEquals(2, (entry.fields()["required"] as List<*>).size)
        assertNull(entry.fields()["providers"])
    }

    @Test
    fun anEntryWithoutAProvidersSectionTakesNoOverlay() {
        assertEquals(mapOf("type" to "K"), catalogue.of("T", "Plain")!!.section("key", "P @ android-33"))
    }

    @Test
    fun aProviderRunsAsTheNearestBuildAtOrBelowThePlatform() {
        assertEquals("P @ android-33", catalogue.build("P", "android-33"))
        assertEquals("P @ android-33", catalogue.build("P", "android-37"))
        assertEquals("P @ android-30", catalogue.build("P", "android-31"))
        assertEquals("P @ android-30", catalogue.build("P", "android-26"))
        assertEquals("P @ android-33", catalogue.build("P", "jdk-25"))
        assertEquals("B @ some:artifact:1", catalogue.build("B", "jdk-25"))
        assertNull(catalogue.build("Unmeasured", "android-33"))
    }

    @Test
    fun groupExemplarsByFamily() {
        val groups = GroupExemplars.parse("schemaVersion: 3\ngroups:\n  f.none: {exemplars: [T|A], algorithms: [A]}\n  unidentified: {exemplars: [], algorithms: []}")
        assertEquals(listOf("T|A"), groups.of("f.none"))
        assertEquals(emptyList<String>(), groups.of("other"))
    }
}
