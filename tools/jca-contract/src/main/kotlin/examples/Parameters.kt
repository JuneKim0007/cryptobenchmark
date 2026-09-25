package examples

import java.lang.reflect.Modifier
import java.math.BigInteger
import java.security.spec.AlgorithmParameterSpec

/**
 * What a parameter tree may name, read from the runtime rather than from a table.
 * `./gradlew run -q -PmainClass=examples.ParametersKt` lists every spec class this JVM offers;
 * `--args="javax.crypto.spec.GCMParameterSpec"` prints one class as a YAML block to paste into a test set.
 */
fun main(arguments: Array<String>) {
    val named = arguments.firstOrNull()
    if (named == null) {
        for ((packageName, classes) in specClasses().groupBy { it.packageName }.toSortedMap()) {
            println("## $packageName")
            for (specClass in classes.sortedBy { it.simpleName }) {
                println("${specClass.simpleName}: ${specClass.constructors.size} constructor(s)")
            }
            println()
        }
        println("# name one to see its arguments, e.g. --args=\"javax.crypto.spec.GCMParameterSpec\"")
        return
    }
    val specClass = runCatching { Class.forName(named) }.getOrNull()
        ?: return println("no class $named on this runtime")
    println("# $named")
    val constructors = specClass.constructors.sortedBy { it.parameterCount }
    for (constructor in constructors) {
        println("#   (${constructor.parameterTypes.joinToString(", ") { it.simpleName }})")
    }
    println("# allowed by the binder: ${allowed(specClass)}")
    for (parameterType in constructors.flatMap { it.parameterTypes.toList() }.distinct()) {
        val buildable = parameterType.isPrimitive || parameterType.isArray || parameterType == String::class.java
        if (!buildable && (parameterType.isInterface || Modifier.isAbstract(parameterType.modifiers) || parameterType.constructors.isEmpty())) {
            val candidates = concreteKinds(parameterType)
            if (candidates.size > 8) {
                println("# ${parameterType.simpleName} cannot be built directly; ${candidates.size} kinds on this runtime, run with no arguments to list them")
            } else {
                println("# ${parameterType.simpleName} cannot be built directly; this runtime offers: ${candidates.joinToString(", ")}")
            }
        }
    }
    val shortest = constructors.firstOrNull() ?: return
    println()
    println("parameters:")
    println("  class: $named")
    println("  arguments: [${shortest.parameterTypes.joinToString(", ") { example(it) }}]")
    for (longer in constructors.drop(1)) {
        println("# or ${longer.parameterCount} arguments: [${longer.parameterTypes.joinToString(", ") { example(it) }}]")
    }
}

private fun specClasses(): List<Class<*>> {
    return classNamesInJavaBase().mapNotNull { runCatching { Class.forName(it) }.getOrNull() }
        .filter { AlgorithmParameterSpec::class.java.isAssignableFrom(it) && !it.isInterface && !Modifier.isAbstract(it.modifiers) }
}

private fun classNamesInJavaBase(): List<String> {
    val module = java.lang.module.ModuleFinder.ofSystem().find("java.base").orElse(null) ?: return emptyList()
    module.open().use { reader ->
        return reader.list()
            .filter { it.endsWith(".class") && (it.startsWith("java/security/spec/") || it.startsWith("javax/crypto/spec/")) }
            .map { it.removeSuffix(".class").replace('/', '.') }
            .toList()
    }
}

private fun concreteKinds(parameterType: Class<*>): List<String> {
    val classes = classNamesInJavaBase().mapNotNull { runCatching { Class.forName(it) }.getOrNull() }
    val subtypes = classes.filter { parameterType.isAssignableFrom(it) && it != parameterType && !it.isInterface && !Modifier.isAbstract(it.modifiers) }
    val staticFields = classes.flatMap { holder ->
        holder.fields.filter { Modifier.isStatic(it.modifiers) && parameterType.isAssignableFrom(it.type) }
            .map { "{field: ${holder.name}.${it.name}}" }
    }
    return (subtypes.map { it.name } + staticFields).distinct()
}

private fun allowed(specClass: Class<*>): Boolean =
    AlgorithmParameterSpec::class.java.isAssignableFrom(specClass) ||
        BigInteger::class.java.isAssignableFrom(specClass) ||
        specClass.name == "javax.crypto.spec.PSource"

private fun example(parameterType: Class<*>): String = when (parameterType.simpleName) {
    "int", "Integer" -> "<int>"
    "long", "Long" -> "<long>"
    "byte[]" -> "fresh(<n>)"
    "String" -> "<name>"
    "BigInteger" -> "<number>"
    else -> "{class: ${parameterType.name}, arguments: []}"
}
