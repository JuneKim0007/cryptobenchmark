package io.github.junekim0007.cryptobench.architecture

import com.tngtech.archunit.core.importer.ClassFileImporter
import com.tngtech.archunit.library.freeze.FreezingArchRule.freeze
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Paths

class ArchitectureTest {

    @Test
    fun everyModuleHasClasses() {
        val names = ClassEdges.of(classes, layers.root).flatMap { listOf(it.from, it.to) }.toSet()
        layers.uses.keys.forEach { module -> assertTrue("no_classes: $module", names.any { layers.moduleOf(it) == module }) }
    }

    @Test
    fun moduleEdges() = freeze(rules.moduleEdges()).check(classes)

    @Test
    fun handoff() = freeze(rules.handoff()).check(classes)

    @Test
    fun forbidden() = freeze(rules.forbidden()).check(classes)

    @Test
    fun packageCycles() = layers.cycles.forEach { freeze(rules.cycles(it)).check(classes) }

    companion object {
        private val layers = Layers.read(File(System.getProperty("architecture.layers")))
        private val rules = LayerRules(layers)
        private val classes = ClassFileImporter().importPaths(System.getProperty("architecture.classes").split(File.pathSeparator).map { Paths.get(it) })
    }
}
