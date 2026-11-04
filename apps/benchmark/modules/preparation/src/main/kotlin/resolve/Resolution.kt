package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase

data class Resolution(
    val cases: List<BenchmarkCase>,
    val rejections: List<Rejection>,
)
