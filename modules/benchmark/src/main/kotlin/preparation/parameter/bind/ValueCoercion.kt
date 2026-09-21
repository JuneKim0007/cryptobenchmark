package io.github.junekim0007.cryptobench.benchmark.preparation.parameter.bind

import java.math.BigInteger

/** YAML gives Integer, Long, BigInteger, String, byte[] and lists; constructors want exact Java types. */
internal object ValueCoercion {

    object NoMatch

    fun to(value: Any, target: Class<*>): Any = when {
        boxed(target).isInstance(value) -> value
        value is Number && (target == Int::class.javaPrimitiveType || target == Int::class.javaObjectType) ->
            exact(value)?.takeIf { it in Int.MIN_VALUE..Int.MAX_VALUE }?.toInt() ?: NoMatch
        value is Number && (target == Long::class.javaPrimitiveType || target == Long::class.javaObjectType) -> exact(value) ?: NoMatch
        value is Number && target == BigInteger::class.java -> if (value is BigInteger) value else exact(value)?.let { BigInteger.valueOf(it) } ?: NoMatch
        value is List<*> && target == ByteArray::class.java -> bytes(value) ?: NoMatch
        else -> NoMatch
    }

    private fun exact(value: Number): Long? = when (value) {
        is Int, is Long, is Short, is Byte -> value.toLong()
        is BigInteger -> if (value.bitLength() < 64) value.toLong() else null
        else -> null
    }

    private fun bytes(values: List<*>): ByteArray? {
        val numbers = values.map { (it as? Number)?.toInt()?.takeIf { value -> value in -128..255 } ?: return null }
        return ByteArray(numbers.size) { index -> numbers[index].toByte() }
    }

    private fun boxed(type: Class<*>): Class<*> = when (type) {
        Int::class.javaPrimitiveType -> Int::class.javaObjectType
        Long::class.javaPrimitiveType -> Long::class.javaObjectType
        Boolean::class.javaPrimitiveType -> Boolean::class.javaObjectType
        Short::class.javaPrimitiveType -> Short::class.javaObjectType
        Byte::class.javaPrimitiveType -> Byte::class.javaObjectType
        Double::class.javaPrimitiveType -> Double::class.javaObjectType
        else -> type
    }
}
