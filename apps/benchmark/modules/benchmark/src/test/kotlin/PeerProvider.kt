package io.github.junekim0007.cryptobench.benchmark

import java.nio.ByteBuffer
import java.security.Key
import java.security.MessageDigest
import java.security.MessageDigestSpi
import java.security.Provider
import java.security.Security
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Mac
import javax.crypto.MacSpi

/** A second provider for the cross-provider tests: SHA-256 and HmacSHA256 delegated to the JDK's own, so a peer exists on a bare JDK. */
class PeerProvider : Provider(NAME, "1", "cross-provider test peer") {

    init {
        put("MessageDigest.SHA-256", Sha256::class.java.name)
        put("Mac.HmacSHA256", HmacSha256::class.java.name)
    }

    class Sha256 : MessageDigestSpi() {
        private val inner = MessageDigest.getInstance("SHA-256", "SUN")
        override fun engineUpdate(input: Byte) = inner.update(input)
        override fun engineUpdate(input: ByteArray, offset: Int, len: Int) = inner.update(input, offset, len)
        override fun engineDigest(): ByteArray = inner.digest()
        override fun engineReset() = inner.reset()
    }

    class HmacSha256 : MacSpi() {
        private val inner = Mac.getInstance("HmacSHA256", "SunJCE")
        override fun engineGetMacLength() = inner.macLength
        override fun engineInit(key: Key, params: AlgorithmParameterSpec?) = inner.init(key, params)
        override fun engineUpdate(input: Byte) = inner.update(input)
        override fun engineUpdate(input: ByteArray, offset: Int, len: Int) = inner.update(input, offset, len)
        override fun engineUpdate(input: ByteBuffer) = inner.update(input)
        override fun engineDoFinal(): ByteArray = inner.doFinal()
        override fun engineReset() = inner.reset()
    }

    companion object {
        const val NAME = "CheckPeer"

        fun <T> installed(block: () -> T): T {
            Security.addProvider(PeerProvider())
            try {
                return block()
            } finally {
                Security.removeProvider(NAME)
            }
        }
    }
}
