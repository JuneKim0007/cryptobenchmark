package io.github.junekim0007.cryptobench.preparation.record

import java.security.MessageDigest

internal object Fingerprint {

    private const val CHARACTERS = 8

    fun of(text: String): String =
        MessageDigest.getInstance("SHA-256").digest(text.toByteArray(Charsets.UTF_8))
            .joinToString("") { byte -> "%02x".format(byte) }
            .take(CHARACTERS)
}
