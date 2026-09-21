package io.github.junekim0007.cryptobench.benchmark.preparation.measurement

enum class Phase {
    /** Steady state: the instance is built before the timer, Jetpack Microbenchmark measures the loop. */
    WARM,

    /** First call in a fresh process, timed once per process; not a Jetpack Microbenchmark measurement. */
    COLD,
}
