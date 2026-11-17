package io.github.junekim0007.cryptobench.preparation.measurement

import io.github.junekim0007.cryptobench.files.VariantLabels

enum class Variant(val label: String) {
    FIXED(VariantLabels.FIXED),
    NOT_FIXED(VariantLabels.NOT_FIXED),
    SECURE(VariantLabels.SECURE);

    companion object {

        fun of(label: String): Variant = entries.firstOrNull { it.label == label }
            ?: throw IllegalArgumentException("unknown_variant: $label, one of ${entries.map { it.label }}")
    }
}
