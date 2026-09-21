package io.github.junekim0007.cryptobench.preparation.input

import java.util.Random

object InputBytes {

    fun of(seed: Long, size: Int): ByteArray = ByteArray(size).also { Random(seed).nextBytes(it) }
}
