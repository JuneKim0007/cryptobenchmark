package io.github.junekim0007.cryptobench.discovery.adapter

/** Single source of truth for attribute typing. */
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

        /** @throws NumberFormatException when an INT attribute does not hold a number. */
        fun parse(attribute: String, raw: String): Any = when (of(attribute)) {
            LIST -> splitPipe(raw)
            INT -> raw.trim().toInt()
            BOOL -> raw.trim().toBoolean()
            STRING -> raw
        }

        fun splitPipe(raw: String): List<String> =
            raw.split('|').map { it.trim() }.filter { it.isNotEmpty() }
    }
}
