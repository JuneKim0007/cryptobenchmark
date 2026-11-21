package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.check.Refusal
import io.github.junekim0007.cryptobench.records.Skip

// skipped: each case's refusal as skipped.yaml records it, when every case was refused and no refusal is run-wide
class RefusedPlanException(val refusals: List<Refusal>, val skipped: List<Skip> = emptyList()) :
    IllegalStateException("refused_plan: ${refusals.joinToString("; ")}")
