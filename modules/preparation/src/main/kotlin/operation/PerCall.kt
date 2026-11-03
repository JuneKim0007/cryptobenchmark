package io.github.junekim0007.cryptobench.preparation.operation

/** What one timed call does; everything before it in this list is done once, outside the timer. */
enum class PerCall(val label: String) {
    OPERATION("operation"),
    INIT_AND_OPERATION("initAndOperation"),
    INSTANCE_INIT_AND_OPERATION("getInstanceInitAndOperation");

    companion object {

        fun of(label: String): PerCall = entries.firstOrNull { it.label == label }
            ?: throw IllegalArgumentException("unknown_per_call: $label, one of ${entries.map { it.label }}")
    }
}
