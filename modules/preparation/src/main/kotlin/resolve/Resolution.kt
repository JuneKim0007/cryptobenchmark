package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase

/** Every case that will run, and every rejection, collected together rather than failing on the first. */
data class Resolution(
    val cases: List<BenchmarkCase>,
    val rejections: List<Rejection>,
)
