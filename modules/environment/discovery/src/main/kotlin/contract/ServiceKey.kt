package io.github.junekim0007.cryptobench.discovery.contract

import java.util.Locale

internal class ServiceKeyException(message: String) : IllegalArgumentException(message)

internal class ServiceKey(type: String, algorithm: String) {

    val type: String = validated("type", type)

    val algorithm: String = validated("algorithm", algorithm)

    override fun equals(other: Any?): Boolean =
        other is ServiceKey && type == other.type && algorithm == other.algorithm

    override fun hashCode(): Int = 31 * type.hashCode() + algorithm.hashCode()

    override fun toString(): String = "$type.$algorithm"

    companion object {

        fun fold(value: String): String = value.uppercase(Locale.ROOT)

        private fun validated(field: String, value: String): String {
            if (value.isBlank()) {
                throw ServiceKeyException("missing_field: $field")
            }
            return fold(value)
        }
    }
}
