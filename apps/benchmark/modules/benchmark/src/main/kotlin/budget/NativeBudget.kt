package io.github.junekim0007.cryptobench.benchmark.budget

/**
 * A benchmark calls far faster than an app, so native contexts freed only by finalize() (Conscrypt's HMAC_CTX, one per init) pile up
 * behind the one FinalizerDaemon until the process aborts. Every [calls] timed calls the caller pauses its timer and runs [clean]:
 * a GC and the finalizers, which return that memory. Every engine type gets it; what it cost is reported beside the median.
 */
class NativeBudget(private val calls: Int = CALLS) {

    private var sinceCleanup = 0
    private var cleanups = 0
    private var pausedNanos = 0L

    // One timed call made; true when the budget is spent and the caller should pause its timer and clean.
    fun due(): Boolean {
        if (++sinceCleanup < calls) return false
        sinceCleanup = 0
        return true
    }

    @Suppress("DEPRECATION")
    fun clean(): Long {
        val start = System.nanoTime()
        System.gc()
        System.runFinalization()
        val paused = System.nanoTime() - start
        cleanups++
        pausedNanos += paused
        return paused
    }

    val spent: NativeCleanup get() = NativeCleanup(calls, cleanups, pausedNanos)

    companion object {
        // About 55 MB of native contexts at roughly 1.1 KB each (emulator API 33, runs/2026-11-07-hmac-oom).
        const val CALLS = 50_000
    }
}
