package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.check.Refusal

class RefusedPlanException(val refusals: List<Refusal>) :
    IllegalStateException("refused_plan: ${refusals.joinToString("; ")}")
