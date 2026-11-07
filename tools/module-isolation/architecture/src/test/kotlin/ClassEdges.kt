package io.github.junekim0007.cryptobench.architecture

import com.tngtech.archunit.core.domain.JavaClasses

data class ClassEdge(val from: String, val to: String)

object ClassEdges {
    fun of(classes: JavaClasses, root: String): Set<ClassEdge> = classes.flatMap { origin ->
        val from = projectName(origin.name, root) ?: return@flatMap emptyList()
        origin.directDependenciesFromSelf.mapNotNull { dependency ->
            projectName(dependency.targetClass.baseComponentType.name, root)?.takeIf { it != from }?.let { ClassEdge(from, it) }
        }
    }.toSortedSet(compareBy({ it.from }, { it.to }))

    private fun projectName(name: String, root: String): String? =
        name.takeIf { it.startsWith("$root.") }?.removePrefix("$root.")?.substringBefore('$')
}
