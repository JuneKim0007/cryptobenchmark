package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.entry.KeySource
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.files.ContractsFolder
import org.junit.Assert.assertEquals
import org.junit.Test
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor
import org.yaml.snakeyaml.nodes.MappingNode
import org.yaml.snakeyaml.nodes.Node
import org.yaml.snakeyaml.nodes.NodeTuple
import org.yaml.snakeyaml.nodes.ScalarNode
import org.yaml.snakeyaml.nodes.SequenceNode
import java.io.StringReader

/** Every key the global and test-set readers accept is written, with a comment on its line, in config's examples: a reader's new key with no example line fails. */
class ExampleCoverageTest {

    private class Shape(val path: String, val known: List<String>, val present: MutableSet<String> = linkedSetOf())

    private val shapes = LinkedHashMap<List<String>, Shape>()
    private val uncommented = mutableListOf<String>()
    private val unlisted = mutableListOf<String>()
    private val keyBlock = linkedSetOf<String>()

    @Test
    fun everyAcceptedKeyIsInAnExampleWithItsComment() {
        walk("config_global_example.yaml") { GlobalDocument.parse(it) }
        walk("config_testset_example.yaml") { TestSetDocument.parse(it) }
        assertEquals("keys a reader accepts that no example writes", emptyList<String>(), shapes.values.flatMap { s -> (s.known - s.present).map { "${s.path}.$it" } })
        assertEquals("example keys with no comment on their line", emptyList<String>(), uncommented)
        assertEquals("key source keys no set.key writes", emptyList<String>(), KeySource.KEYS - keyBlock)
        assertEquals("mappings off the open list whose reader names no key list", emptyList<String>(), unlisted.map { "$it: no key list in the refusal" })
    }

    private fun walk(name: String, parse: (Map<String, Any>) -> Unit) {
        val text = ContractsFolder.example("config", name).readText()
        visit(Yaml().compose(StringReader(text)), emptyList(), name, text.lines()) { path -> accepted(text, path, parse) }
    }

    private fun visit(node: Node, path: List<Any>, name: String, lines: List<String>, known: (List<Any>) -> List<String>?) {
        val schema = path.joinToString("") { if (it is Int) "[]" else ".$it" }.removePrefix(".")
        if (schema == KEY_BLOCK && node is MappingNode) keyBlock += node.value.map { (it.keyNode as ScalarNode).value }
        if (OPEN.any { schema == it || schema.startsWith("$it.") || schema.startsWith("$it[") }) return
        when (node) {
            is MappingNode -> {
                val keys = node.value.map { (it.keyNode as ScalarNode).value to it }
                val label = "$name.$schema".removeSuffix(".")
                val accepted = known(path)
                if (accepted == null) unlisted += label
                else shapes.getOrPut(accepted.sorted()) { Shape(label, accepted) }.present += keys.map { it.first }
                uncommented += keys.filterNot { (_, tuple) -> commented(tuple, lines) }.map { "$label.${it.first}" }
                keys.forEach { (key, tuple) -> visit(tuple.valueNode, path + key, name, lines, known) }
            }
            is SequenceNode -> node.value.forEachIndexed { index, item -> visit(item, path + index, name, lines, known) }
            else -> Unit
        }
    }

    // a comment is a whitespace-led # after the value, or after the key when the value starts below it
    private fun commented(tuple: NodeTuple, lines: List<String>): Boolean {
        val key = tuple.keyNode.endMark
        val value = tuple.valueNode.endMark
        val from = if (value.line == key.line) value.column else key.column
        return COMMENT.containsMatchIn(lines[key.line].substring(from))
    }

    /** The keys the reader names when the mapping at path holds one it does not know; null when no refusal names them. */
    @Suppress("UNCHECKED_CAST")
    private fun accepted(text: String, path: List<Any>, parse: (Map<String, Any>) -> Unit): List<String>? {
        val document = Yaml(SafeConstructor(LoaderOptions())).load<Map<String, Any>>(text)
        val target = path.fold<Any, Any>(document) { at, step -> if (step is Int) (at as List<Any>)[step] else (at as Map<String, Any>).getValue(step as String) }
        (target as MutableMap<String, Any>)[PROBE] = emptyMap<String, Any>()
        val message = try {
            parse(document)
            return null
        } catch (failure: RuntimeException) {
            generateSequence<Throwable>(failure) { it.cause }.mapNotNull { it.message }.firstOrNull { PROBE in it } ?: return null
        }
        return KNOWN.find(message)?.groupValues?.get(1)?.split(", ")
    }

    private companion object {
        const val PROBE = "exampleCoverageProbe"
        val KNOWN = Regex("""known \[([^\]]*)]""")
        val COMMENT = Regex("""\s#""")
        // readers that take any key: preparation's parameter tree, and a key block beside its spec tree
        const val KEY_BLOCK = "overrides[].set.key"
        val OPEN = setOf("overrides[].set.parameters", KEY_BLOCK)
    }
}
