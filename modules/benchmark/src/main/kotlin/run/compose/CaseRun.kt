package io.github.junekim0007.cryptobench.benchmark.run.compose

// Returns the calls made, or null when the harness that ran it counts them (Jetpack).
fun interface CaseRun {
    fun run(): Long?
}
