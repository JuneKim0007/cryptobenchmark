package io.github.junekim0007.cryptobench.architecture

import org.junit.Assert.assertEquals
import org.junit.Test

class LayersTest {

    @Test
    fun aListedNameWithoutItsClassIsStale() {
        val layers = Layers("io.x", mapOf("prep" to mapOf("files" to setOf("Names", "gone.Old"), "doc" to null)), emptyList(), emptyList(),
            mapOf("cli" to mapOf("prep" to setOf("plan.Plan", "plan"))))
        assertEquals(listOf("stale_entry: prep uses files.gone.Old: no such class in files", "stale_entry: cli uses prep.plan: no such class in prep"),
            layers.staleEntries(setOf("files.Names", "prep.plan.Plan")))
    }
}
