package io.github.junekim0007.cryptobench.architecture

import com.tngtech.archunit.core.domain.JavaClasses
import com.tngtech.archunit.lang.AbstractClassesTransformer
import com.tngtech.archunit.lang.ArchCondition
import com.tngtech.archunit.lang.ArchRule
import com.tngtech.archunit.lang.ConditionEvents
import com.tngtech.archunit.lang.SimpleConditionEvent
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition

class LayerRules(private val layers: Layers) {

    fun moduleEdges(): ArchRule = classEdgeRule("use only the modules layers.yaml lists for their module") { from, to, edge ->
        "${edge.from} -> ${edge.to}".takeIf { from != to && to !in layers.uses.getValue(from) }
    }

    fun handoff(): ArchRule = classEdgeRule("reach another module only through its handoff classes in layers.yaml") { from, to, edge ->
        val names = layers.uses.getValue(from)[to] ?: return@classEdgeRule null
        "${edge.from} -> ${edge.to}".takeIf { edge.to.removePrefix("$to.") !in names }
    }

    fun forbidden(): ArchRule = classEdgeRule("not use a package layers.yaml forbids") { _, _, edge ->
        layers.forbidden.firstOrNull { it.covers(edge.from) && it.targets(edge.to) }
            ?.let { "${edge.from} -> ${edge.to} (${it.from} must not use ${it.to})" }
    }

    fun cycles(granularity: String): ArchRule {
        val node: (String) -> String = when (granularity) {
            "package" -> { packageName -> packageName }
            "top-level" -> { packageName -> packageName.substringBefore('.') }
            else -> error("unknown_granularity: $granularity")
        }
        return rule("$granularity package edges", "not lie on a cycle within their module", { classes ->
            moduleGraph(classes, node).flatMap { (module, edges) -> CycleEdges.of(edges).map { "$module: ${it.first} -> ${it.second}" } }
        })
    }

    private fun moduleGraph(classes: JavaClasses, node: (String) -> String): Map<String, Set<Pair<String, String>>> =
        ClassEdges.of(classes, layers.root).mapNotNull { edge ->
            val module = layers.moduleOf(edge.from)?.takeIf { it == layers.moduleOf(edge.to) } ?: return@mapNotNull null
            val pair = node(packageIn(module, edge.from)) to node(packageIn(module, edge.to))
            (module to pair).takeIf { pair.first != pair.second }
        }.groupBy({ it.first }, { it.second }).mapValues { it.value.toSet() }

    private fun packageIn(module: String, className: String): String =
        className.removePrefix("$module.").substringBeforeLast('.', "(root)")

    private fun classEdgeRule(should: String, violation: (String, String, ClassEdge) -> String?): ArchRule =
        rule("project class edges", should, { classes ->
            ClassEdges.of(classes, layers.root).mapNotNull { edge ->
                val from = layers.moduleOf(edge.from) ?: return@mapNotNull null
                val to = layers.moduleOf(edge.to) ?: return@mapNotNull null
                violation(from, to, edge)
            }
        })

    private fun rule(items: String, should: String, find: (JavaClasses) -> List<String>): ArchRule =
        ArchRuleDefinition.all(object : AbstractClassesTransformer<String>(items) {
            override fun doTransform(classes: JavaClasses): Iterable<String> = find(classes)
        }).should(object : ArchCondition<String>(should) {
            override fun check(item: String, events: ConditionEvents) = events.add(SimpleConditionEvent.violated(item, item))
        }).allowEmptyShould(true)
}
