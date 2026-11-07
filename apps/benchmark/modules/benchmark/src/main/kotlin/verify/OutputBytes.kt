package io.github.junekim0007.cryptobench.benchmark.verify

import java.security.Key
import java.security.KeyPair
import java.security.MessageDigest

/** A call's output as bytes where it has them, and their SHA-256 for a record. */
object OutputBytes {

    fun of(output: Any?): ByteArray? = when (output) {
        is ByteArray -> output
        is Key -> output.encoded
        is KeyPair -> output.public.encoded
        else -> null
    }

    fun digest(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
}
