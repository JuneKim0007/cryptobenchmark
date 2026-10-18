package io.github.junekim0007.cryptobench

/** The calling thread's core affinity, through libaffinity.so (src/main/cpp). */
object Affinity {

    init {
        System.loadLibrary("affinity")
    }

    /** 0 when the thread is pinned, else the errno. */
    external fun pin(core: Int): Int

    /** Bit n set when core n is allowed; -1 when it cannot be read. */
    external fun allowed(): Long

    /** Allows exactly the cores in mask again; 0 or the errno. */
    external fun restore(mask: Long): Int

    external fun current(): Int
}
