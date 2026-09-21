package io.github.junekim0007.cryptobench.benchmark.preparation.measurement

enum class Metric {
    TIME,
    ALLOCATION,

    /** Instructions and cycles through androidx.benchmark.cpuEventCounter; needs a rooted device. */
    CPU_EVENTS,
}
