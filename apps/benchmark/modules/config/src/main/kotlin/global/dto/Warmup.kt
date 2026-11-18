package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.config.testset.dto.Rule

/** run.warmup: a pre-flight run of a few cases before a device session's first pass; never measured, iterations 0 turns it off; cases: how many of
 * the plan's first cases it warms when jobs is empty. */
data class Warmup(val iterations: Int = ITERATIONS, val jobs: List<Rule> = emptyList(), val cases: Int = CASES) {

    init {
        require(iterations >= 0) { "negative: run.warmup.iterations $iterations" }
        require(cases >= 1) { "not_positive: run.warmup.cases $cases" }
    }

    companion object {
        const val ITERATIONS = 10
        const val CASES = 3
    }
}
