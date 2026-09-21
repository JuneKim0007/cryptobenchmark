package io.github.junekim0007.cryptobench.discovery.adapter

internal enum class AttributeKind {
    LIST, INT, BOOL, STRING;

    companion object {

        private val KINDS = mapOf(
            "SupportedModes" to LIST,
            "SupportedPaddings" to LIST,
            "SupportedKeyClasses" to LIST,
            "SupportedKeyFormats" to LIST,
            "SupportedCurves" to LIST,
            "KeySize" to INT,
            "ThreadSafe" to BOOL,
            "ImplementedIn" to STRING,
            "MechanismType" to STRING,
        )

        fun of(attribute: String): AttributeKind = KINDS[attribute] ?: STRING
    }
}
