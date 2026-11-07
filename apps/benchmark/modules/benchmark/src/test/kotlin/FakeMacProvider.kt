package io.github.junekim0007.cryptobench.benchmark

import java.security.Key
import java.security.MessageDigest
import java.security.Provider
import java.security.SecureRandom
import java.security.Security
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.MacSpi
import javax.crypto.spec.IvParameterSpec

/** Two GMAC-named Macs for the repeat property: one random by bug, one whose tag is fixed by its nonce and message. */
class FakeMacProvider : Provider(NAME, "1", "repeat property test Macs") {

    init {
        put("Mac.$RANDOM", RandomMac::class.java.name)
        put("Mac.$NONCE_KEYED", NonceKeyedMac::class.java.name)
    }

    abstract class SixteenByteMac : MacSpi() {
        protected var nonce = ByteArray(0)
        protected val message = java.io.ByteArrayOutputStream()
        override fun engineGetMacLength() = 16
        override fun engineInit(key: Key, params: AlgorithmParameterSpec?) {
            nonce = (params as? IvParameterSpec)?.iv ?: ByteArray(0)
            message.reset()
        }
        override fun engineUpdate(input: Byte) = message.write(input.toInt())
        override fun engineUpdate(input: ByteArray, offset: Int, len: Int) = message.write(input, offset, len)
        override fun engineReset() = message.reset()
    }

    class RandomMac : SixteenByteMac() {
        override fun engineDoFinal(): ByteArray = ByteArray(16).also { SecureRandom().nextBytes(it); message.reset() }
    }

    class NonceKeyedMac : SixteenByteMac() {
        override fun engineDoFinal(): ByteArray =
            MessageDigest.getInstance("SHA-256").run { update(nonce); digest(message.toByteArray()) }.copyOf(16).also { message.reset() }
    }

    companion object {
        const val NAME = "CheckFakeMac"
        const val RANDOM = "Random-GMAC"
        const val NONCE_KEYED = "NonceKeyed-GMAC"

        fun <T> installed(block: () -> T): T {
            Security.addProvider(FakeMacProvider())
            try {
                return block()
            } finally {
                Security.removeProvider(NAME)
            }
        }
    }
}
