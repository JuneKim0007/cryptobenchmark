package io.github.junekim0007.cryptobench.settings

/** cpu.core: one core index, or Big, the highest-frequency online core that facts resolve to an index. */
sealed interface CoreChoice {

    data class Index(val index: Int) : CoreChoice {
        init {
            require(index in 0..MAX_INDEX) { invalid(LABEL, index) }
        }

        override fun toString(): String = index.toString()
    }

    data object Big : CoreChoice {
        override fun toString(): String = BIG
    }

    companion object {
        const val BIG = "big"
        const val MAX_INDEX = 63
        private const val LABEL = "cpu.core"

        /** A number or a word; anything else is refused with its code. */
        fun read(value: Any, label: String): CoreChoice {
            val text = when (value) {
                is Number -> value.toDouble().takeIf { it % 1.0 == 0.0 }?.toLong()?.toString() ?: value.toString()
                is String -> value
                else -> throw Values.wrongType(label, "a number or a word", value)
            }
            if (text == BIG) return Big
            val index = text.toIntOrNull()?.takeIf { it in 0..MAX_INDEX } ?: throw IllegalArgumentException(invalid(label, text))
            return Index(index)
        }

        fun write(choice: CoreChoice): Any = when (choice) {
            is Index -> choice.index
            Big -> BIG
        }

        private fun invalid(label: String, value: Any) = "invalid: $label $value, an index 0..$MAX_INDEX or $BIG"
    }
}
