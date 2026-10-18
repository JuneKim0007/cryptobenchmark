package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.settings.CpuRequest
import java.io.File

/** The cpu setting's handler: choose the core, pin the measuring thread, read the affinity back, and undo it after the case. */
class CorePin private constructor(private val previous: Long?, val outcome: Outcome) : AutoCloseable {

    sealed interface Outcome {
        data class Applied(val core: Int) : Outcome
        data class Failed(val reason: String) : Outcome
    }

    override fun close() {
        previous?.let { Affinity.restore(it) }
    }

    companion object {
        private val CORE = Regex("cpu[0-9]+")

        fun apply(request: CpuRequest): CorePin {
            val core = if (request.core == CpuRequest.BIG) bigCore() ?: return failed("no_frequencies: no core reports cpuinfo_max_freq")
            else request.core.toInt()
            val previous = try {
                Affinity.allowed()
            } catch (missing: LinkageError) {
                return failed("no_pinning: ${missing.message}")
            } catch (missing: ExceptionInInitializerError) {
                return failed("no_pinning: ${missing.cause?.message}")
            }
            val error = Affinity.pin(core)
            if (error != 0) return CorePin(previous, Outcome.Failed("pin_failed: core $core, errno $error"))
            val now = Affinity.allowed()
            if (now != 1L shl core) return CorePin(previous, Outcome.Failed("not_pinned: core $core, allowed ${java.lang.Long.toBinaryString(now)}"))
            return CorePin(previous, Outcome.Applied(core))
        }

        private fun failed(reason: String) = CorePin(null, Outcome.Failed(reason))

        /** The online core with the highest cpuinfo_max_freq; the highest index on a tie. */
        private fun bigCore(): Int? = File("/sys/devices/system/cpu").listFiles { file -> CORE.matches(file.name) }
            ?.mapNotNull { dir -> File(dir, "cpufreq/cpuinfo_max_freq").takeIf { it.canRead() }?.readText()?.trim()?.toLongOrNull()?.let { dir.name.drop(3).toInt() to it } }
            ?.maxWithOrNull(compareBy({ it.second }, { it.first }))?.first
    }
}
