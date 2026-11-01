package io.github.junekim0007.cryptobench

import java.util.Random
import javax.crypto.spec.SecretKeySpec

/** Seeded inputs for generated scopes: one seed gives the same values on every run and device. */
object ScopeInputs {

    private const val ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    fun bytes(size: Int, seed: Long): ByteArray = ByteArray(size).also(Random(seed)::nextBytes)

    fun text(size: Int, seed: Long): String {
        val random = Random(seed)
        return String(CharArray(size) { ALPHABET[random.nextInt(ALPHABET.length)] })
    }

    fun chars(size: Int, seed: Long): CharArray = text(size, seed).toCharArray()

    fun secretKey(algorithm: String, bits: Int, seed: Long): SecretKeySpec = SecretKeySpec(bytes(bits / 8, seed), algorithm)
}
