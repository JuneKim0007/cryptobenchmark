package io.github.junekim0007.cryptobench.benchmark.preparation.measurement

internal object CaseName {

    private val UNSAFE = Regex("[^A-Za-z0-9]")

    fun of(case: BenchmarkCase): String = listOfNotNull(
        case.type,
        case.algorithm,
        case.provider,
        case.keySize?.let { "k$it" },
        case.inputSize?.let { "i$it" },
        case.phase.name,
    ).joinToString("_") { part -> part.replace(UNSAFE, "-") }
}
