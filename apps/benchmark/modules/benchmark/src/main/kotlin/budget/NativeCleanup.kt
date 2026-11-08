package io.github.junekim0007.cryptobench.benchmark.budget

/** What a case's [NativeBudget] cost: the paused cleanups and their time, outside every timed sample; benchmark.json's `nativeCleanup`. */
data class NativeCleanup(val everyCalls: Int, val cleanups: Int, val pausedNanos: Long) {

    // Merged processes or passes: the counts and the paused time add up.
    fun mergedWith(later: NativeCleanup): NativeCleanup = NativeCleanup(everyCalls, cleanups + later.cleanups, pausedNanos + later.pausedNanos)

    fun toMap(): Map<String, Any> = linkedMapOf(EVERY_CALLS to everyCalls, CLEANUPS to cleanups, PAUSED_NANOS to pausedNanos)

    companion object {
        const val FIELD = "nativeCleanup"
        private const val EVERY_CALLS = "everyCalls"
        private const val CLEANUPS = "cleanups"
        private const val PAUSED_NANOS = "pausedNanos"

        fun read(value: Any?): NativeCleanup? {
            val fields = value as? Map<*, *> ?: return null
            fun number(key: String) = (fields[key] as? Number) ?: throw IllegalArgumentException("missing_field: $FIELD.$key")
            return NativeCleanup(number(EVERY_CALLS).toInt(), number(CLEANUPS).toInt(), number(PAUSED_NANOS).toLong())
        }
    }
}
