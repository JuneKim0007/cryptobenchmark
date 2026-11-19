package io.github.junekim0007.cryptobench.settings

/** The keys of an effective run section: config writes them, preparation accepts them. */
object RunKeys {
    const val INPUT_SIZES = "inputSizes"
    const val PHASES = "phases"
    const val METRICS = "metrics"
    const val VARIANTS = "variants"
    const val PROCESS_REPETITIONS = "processRepetitions"
    const val SEED = "seed"
    const val PASSES = "passes"
    const val THROTTLE_SLEEP = "thermalThrottleSleepSeconds"
    const val CASE_COOLDOWN = "caseCooldownSeconds"
    const val WARMUP = "warmup"
    const val THERMAL_GATE = "thermalGate"
    const val LAUNCH_RETRIES = "launchRetries"
    const val RESUME_BLOCK_RUNS = "resumeBlockRuns"
    const val ORDER_SEED = "orderSeed"
    const val HARNESS = "harness"

    val ALL = listOf(INPUT_SIZES, PHASES, METRICS, VARIANTS, PROCESS_REPETITIONS, SEED, PASSES, THROTTLE_SLEEP, CASE_COOLDOWN, WARMUP,
                     THERMAL_GATE, LAUNCH_RETRIES, RESUME_BLOCK_RUNS, ORDER_SEED, HARNESS)
}
