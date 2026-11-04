package io.github.junekim0007.cryptobench

/** The calling thread's allowed cores (cores 0..63), through libaffinity.so; loadError keeps why it is unavailable. */
object Affinity {

    val loadError: String? = try {
        System.loadLibrary("affinity")
        null
    } catch (missing: UnsatisfiedLinkError) {
        missing.message ?: "libaffinity.so did not load"
    }

    /** Bit n set when core n is allowed; -1 when it cannot be read. */
    external fun allowed(): Long

    /** Allows exactly the cores in mask; 0 or the errno. */
    external fun allow(mask: Long): Int
}
