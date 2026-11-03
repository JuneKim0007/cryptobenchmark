package io.github.junekim0007.cryptobench

import android.os.Debug
import androidx.benchmark.ExperimentalBenchmarkConfigApi
import androidx.benchmark.MetricCapture

/** Allocation counting inside the timed phase, as androidx's AllocationCountCapture does it, so an allocation pass gets one run per sample. */
@OptIn(ExperimentalBenchmarkConfigApi::class)
@Suppress("DEPRECATION")
class SampledAllocations : MetricCapture(listOf(NAME)) {

    private var pausedAt = 0
    private var paused = 0

    override fun captureStart(timeNs: Long) {
        paused = 0
        Debug.startAllocCounting()
    }

    override fun captureStop(timeNs: Long, output: LongArray, offset: Int) {
        Debug.stopAllocCounting()
        output[offset] = (Debug.getGlobalAllocCount() - paused).toLong()
    }

    override fun capturePaused() {
        pausedAt = Debug.getGlobalAllocCount()
    }

    override fun captureResumed() {
        paused += Debug.getGlobalAllocCount() - pausedAt
    }

    companion object {
        // androidx's own allocation phase writes allocationCount; paired with MetricSamples.SAMPLED_ALLOCATIONS.
        const val NAME = "allocationSamples"
    }
}
