package io.github.junekim0007.cryptobench.preparation.measurement

enum class Variant(val label: String) {
    FIXED("fixed"),
    NOT_FIXED("notFixed");

    companion object {

        fun of(label: String): Variant = entries.firstOrNull { it.label == label }
            ?: throw IllegalArgumentException("unknown_variant: $label, one of ${entries.map { it.label }}")
    }
}
