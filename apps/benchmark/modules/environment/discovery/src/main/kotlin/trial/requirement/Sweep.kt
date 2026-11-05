package io.github.junekim0007.cryptobench.discovery.trial.requirement

// An accepted set read from single calls, written as ranges so a 64-step sweep stays one line.
internal object Sweep {

    fun of(values: Iterable<Int>, call: (Int) -> Unit): Map<String, Any> {
        val accepted = mutableListOf<Int>()
        var firstRefusal: String? = null
        for (value in values) {
            val refused = ErrorText.refusal { call(value) }
            if (refused == null) accepted += value else if (firstRefusal == null) firstRefusal = "$value: $refused"
        }
        return linkedMapOf<String, Any>("accepted" to ranges(accepted)).apply { firstRefusal?.let { put("firstRefusal", it) } }
    }

    fun ranges(values: List<Int>): String {
        val parts = mutableListOf<String>()
        var start = 0
        for (index in values.indices) {
            if (index + 1 == values.size || values[index + 1] != values[index] + 1) {
                parts += if (start == index) "${values[index]}" else "${values[start]}-${values[index]}"
                start = index + 1
            }
        }
        return parts.joinToString(",")
    }
}
