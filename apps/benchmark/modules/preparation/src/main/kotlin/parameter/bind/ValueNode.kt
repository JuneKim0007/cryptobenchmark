package io.github.junekim0007.cryptobench.preparation.parameter.bind

import java.lang.reflect.Constructor
import java.lang.reflect.InvocationTargetException
import java.security.SecureRandom

internal sealed class ValueNode {

    abstract val varies: Boolean

    abstract fun evaluate(): Any

    class Literal(private val value: Any) : ValueNode() {
        override val varies: Boolean = false
        override fun evaluate(): Any = value
    }

    class Fresh(private val size: Int, private val random: SecureRandom) : ValueNode() {
        override val varies: Boolean = true
        override fun evaluate(): Any = ByteArray(size).also { random.nextBytes(it) }
    }

    class StaticField(private val value: Any) : ValueNode() {
        override val varies: Boolean = false
        override fun evaluate(): Any = value
    }

    class Construction(
        private val type: Class<*>,
        private val arguments: List<ValueNode>,
        private val path: String,
    ) : ValueNode() {

        override val varies: Boolean = arguments.any { it.varies }

        override fun evaluate(): Any {
            val values = arguments.map { it.evaluate() }
            val attempts = mutableListOf<String>()
            for (constructor in type.constructors.filter { it.parameterCount == values.size }) {
                val coerced = coerce(constructor, values)
                if (coerced == null) {
                    attempts += signature(constructor) + " type mismatch"
                    continue
                }
                try {
                    return constructor.newInstance(*coerced)
                } catch (thrown: InvocationTargetException) {
                    attempts += signature(constructor) + " " + (thrown.cause?.let { it.javaClass.simpleName + ": " + it.message } ?: "failed")
                }
            }
            throw BindException(path, "no constructor of ${type.name} takes ${describe(values)}" +
                if (attempts.isEmpty()) " (none with ${values.size} arguments)" else " -> $attempts")
        }

        private fun coerce(constructor: Constructor<*>, values: List<Any>): Array<Any>? =
            Array(values.size) { index ->
                val converted = ValueCoercion.to(values[index], constructor.parameterTypes[index])
                if (converted === ValueCoercion.NoMatch) return null
                converted
            }

        private fun signature(constructor: Constructor<*>): String =
            constructor.parameterTypes.joinToString(", ", "(", ")") { it.simpleName }

        private fun describe(values: List<Any>): String =
            values.joinToString(", ", "[", "]") { if (it is ByteArray) "byte[${it.size}]" else "${it.javaClass.simpleName} $it" }
    }
}
