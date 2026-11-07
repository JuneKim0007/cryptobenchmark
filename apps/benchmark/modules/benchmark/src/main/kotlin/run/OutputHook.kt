package io.github.junekim0007.cryptobench.benchmark.run

// Check mode only: keeps what each call returned for the checker; a timed run hands its output to a BlackHole and never builds one.
class OutputHook {

    private val received = mutableListOf<Any?>()

    val outputs: List<Any?> get() = received

    fun consume(output: Any?) {
        received += output
    }
}
