package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.config.testset.dto.Rule

/** run.warmup: a pre-flight run of a few cases before a device session's first pass; never measured, iterations 0 turns it off. */
data class Warmup(val iterations: Int = ITERATIONS, val jobs: List<Rule> = emptyList()) {

    init {
        require(iterations >= 0) { "negative: run.warmup.iterations $iterations" }
    }

    companion object {
        const val ITERATIONS = 10
    }
}
