package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.settings.CpuSettings

/** The cpu setting's handler: pin the measuring thread to the resolved core, read it back, and restore the previous cores after the case. */
class CorePin private constructor(private val previous: Long?, val outcome: Outcome) : AutoCloseable {

    sealed interface Outcome {
        data class Applied(val core: Int) : Outcome
        data class Failed(val reason: String) : Outcome
    }

    override fun close() {
        val restore = previous ?: return
        val error = Affinity.allow(restore)
        check(error == 0) { "cpu_restore_failed: errno $error; later cases would run pinned" }
    }

    companion object {

        fun apply(cpu: CpuSettings): CorePin {
            val core = cpu.core?.toIntOrNull() ?: return failed("unresolved: cpu.core ${cpu.core}, effective.yaml should name an index")
            Affinity.loadError?.let { return failed("no_pinning: $it") }
            val previous = Affinity.allowed().takeIf { it != -1L } ?: return failed("affinity_unreadable: sched_getaffinity failed")
            val error = Affinity.allow(1L shl core)
            if (error != 0) return CorePin(previous, Outcome.Failed("pin_failed: core $core, errno $error"))
            val now = Affinity.allowed()
            if (now != 1L shl core) return CorePin(previous, Outcome.Failed("not_pinned: core $core, allowed ${java.lang.Long.toBinaryString(now)}"))
            return CorePin(previous, Outcome.Applied(core))
        }

        private fun failed(reason: String) = CorePin(null, Outcome.Failed(reason))
    }
}
