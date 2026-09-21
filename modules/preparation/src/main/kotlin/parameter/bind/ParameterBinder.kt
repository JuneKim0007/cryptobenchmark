package io.github.junekim0007.cryptobench.preparation.parameter.bind

import java.lang.reflect.Modifier
import java.security.SecureRandom
import java.security.spec.AlgorithmParameterSpec

/**
 * `{class, arguments}` → AlgorithmParameterSpec, by reflection over the fully qualified name. An argument is a literal,
 * `fresh(n)`, `{field: package.Class.NAME}`, or another `{class, arguments}`. Binding builds the spec once, so every
 * mistake surfaces here, in preparation, never inside a measurement.
 */
class ParameterBinder(
    private val random: SecureRandom = SecureRandom(),
    private val policy: BindPolicy = BindPolicy.standard(),
) {

    fun bind(tree: Map<String, Any>, path: String): BoundParameters {
        val root = compile(tree, path)
        val first = root.evaluate()
        if (first !is AlgorithmParameterSpec) {
            throw BindException(path, "${first.javaClass.name} is not an AlgorithmParameterSpec")
        }
        return BoundParameters(root)
    }

    private fun compile(value: Any?, path: String): ValueNode = when {
        value == null -> throw BindException(path, "empty value")
        value is Map<*, *> && value.containsKey(FIELD) -> {
            expectKeys(value, setOf(FIELD), path)
            staticField(value[FIELD] as? String ?: throw BindException(path, "field must be a name"), path)
        }
        value is Map<*, *> && value.containsKey(CLASS) -> {
            expectKeys(value, setOf(CLASS, ARGUMENTS), path)
            val type = permitted(value[CLASS] as? String ?: throw BindException(path, "class must be a name"), path)
            val arguments = (value[ARGUMENTS] ?: emptyList<Any>()) as? List<*> ?: throw BindException("$path.$ARGUMENTS", "must be a list")
            ValueNode.Construction(type, arguments.mapIndexed { index, argument -> compile(argument, "$path.$ARGUMENTS[$index]") }, path)
        }
        value is Map<*, *> -> throw BindException(path, "a map needs '$CLASS' or '$FIELD'")
        value is String && FRESH.matches(value) -> ValueNode.Fresh(FRESH.find(value)!!.groupValues[1].toInt(), random)
        else -> ValueNode.Literal(value)
    }

    /** Loaded without running static initialisers, and refused unless the policy allows the type. */
    private fun permitted(name: String, path: String): Class<*> {
        val type = try {
            Class.forName(name, false, javaClass.classLoader)
        } catch (missing: ClassNotFoundException) {
            throw BindException(path, "no class $name on this runtime")
        }
        if (!policy.permits(type)) {
            throw BindException(path, "$name is not allowed; only subtypes of ${policy.describe()}")
        }
        return type
    }

    private fun staticField(qualified: String, path: String): ValueNode {
        val type = permitted(qualified.substringBeforeLast('.'), path)
        val field = try {
            type.getField(qualified.substringAfterLast('.'))
        } catch (missing: NoSuchFieldException) {
            throw BindException(path, "no public field $qualified")
        }
        if (!Modifier.isStatic(field.modifiers)) {
            throw BindException(path, "$qualified is not static")
        }
        return ValueNode.StaticField(field.get(null))
    }

    private fun expectKeys(value: Map<*, *>, allowed: Set<String>, path: String) {
        val unknown = value.keys.map { it.toString() }.filter { it !in allowed }
        if (unknown.isNotEmpty()) throw BindException(path, "unknown keys $unknown")
    }

    private companion object {
        const val CLASS = "class"
        const val ARGUMENTS = "arguments"
        const val FIELD = "field"
        val FRESH = Regex("""^fresh\((\d+)\)$""")
    }
}
