package io.github.junekim0007.cryptobench.discovery.trial.requirement

// Only keys that need no parameter generation are swept; a size the generator refuses costs one refused call.
internal object PairSizes {

    private val SIZES = listOf(224, 256, 384, 521, 512, 1024, 2048)

    val ALL: List<Int> = SIZES.sorted()
}
