package io.github.junekim0007.cryptobench.discovery.contract

class ServiceAttributes private constructor(private val values: Map<String, Any>) {

    val isEmpty: Boolean get() = values.isEmpty()

    val keySize: Int? get() = integer("KeySize")

    val supportedModes: List<String> get() = strings("SupportedModes")

    val supportedPaddings: List<String> get() = strings("SupportedPaddings")

    private fun integer(name: String): Int? = values[name] as? Int

    @Suppress("UNCHECKED_CAST")
    private fun strings(name: String): List<String> = values[name] as? List<String> ?: emptyList()

    internal fun document(): Map<String, Any> = values

    override fun equals(other: Any?): Boolean =
        other is ServiceAttributes && values == other.values

    override fun hashCode(): Int = values.hashCode()

    override fun toString(): String = values.toString()

    companion object {

        private val EMPTY = ServiceAttributes(emptyMap())

        fun empty(): ServiceAttributes = EMPTY

        fun of(values: Map<String, Any>?): ServiceAttributes =
            if (values.isNullOrEmpty()) EMPTY else ServiceAttributes(values.toSortedMap())
    }
}
