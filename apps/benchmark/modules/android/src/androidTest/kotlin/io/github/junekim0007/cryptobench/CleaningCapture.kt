package io.github.junekim0007.cryptobench

import android.os.Debug
import androidx.benchmark.ExperimentalBenchmarkConfigApi
import androidx.benchmark.MetricCapture
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples

/** Garbage collection between samples. androidx reads the stop time before captureStop and the start time before captureStart, so captureStop is outside every sample. */
@OptIn(ExperimentalBenchmarkConfigApi::class)
class CleaningCapture : MetricCapture(listOf(MetricSamples.GC_PAUSE, MetricSamples.GC_COUNT, MetricSamples.GC_BLOCKING)) {

    private var collections = 0L
    private var blocking = 0L

    // androidx runs one start and stop before the first sample, which sets the counters for it.
    override fun captureStart(timeNs: Long) = Unit

    @Suppress("DEPRECATION")
    override fun captureStop(timeNs: Long, output: LongArray, offset: Int) {
        output[offset + 1] = stat(COLLECTIONS) - collections
        output[offset + 2] = stat(BLOCKING) - blocking
        val start = System.nanoTime()
        Runtime.getRuntime().gc()
        System.runFinalization()
        output[offset] = System.nanoTime() - start
        collections = stat(COLLECTIONS)
        blocking = stat(BLOCKING)
    }

    override fun capturePaused() = Unit

    override fun captureResumed() = Unit

    private fun stat(name: String): Long = Debug.getRuntimeStat(name)?.toLongOrNull() ?: 0L

    private companion object {
        const val COLLECTIONS = "art.gc.gc-count"
        const val BLOCKING = "art.gc.blocking-gc-count"
    }
}
