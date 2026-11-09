package io.github.junekim0007.cryptobench.benchmark.run

/** The host's collection between samples: run with the timer stopped, reported beside the time as android's CleaningCapture does. */
internal class SampleCleaning(private val collectionCount: () -> Long) {

    private val pauses = mutableListOf<Double>()
    private val collections = mutableListOf<Double>()
    private var collectionsAtStart = 0L

    val cleaned: Cleaned get() = Cleaned(pauses, collections)

    @Suppress("DEPRECATION")
    fun beforeSample() {
        val start = System.nanoTime()
        System.gc()
        System.runFinalization()
        pauses += (System.nanoTime() - start).toDouble()
        collectionsAtStart = collectionCount()
    }

    fun afterSample() {
        collections += (collectionCount() - collectionsAtStart).toDouble()
    }
}

/** One value per sample: the forced collection's pause in ns and the collections that landed inside the sample. */
class Cleaned(val pauses: List<Double>, val collections: List<Double>)
