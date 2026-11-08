package io.github.junekim0007.cryptobench.benchmark

import java.security.MessageDigest
import java.security.MessageDigestSpi
import java.security.Provider

/** SHA-256 under three names that fail while armed: an AssertionError, a real StackOverflowError, an IllegalStateException. */
class ThrowingProvider : Provider(NAME, "1", "failure fixture") {

    init {
        put("MessageDigest.$ASSERTION", Asserting::class.java.name)
        put("MessageDigest.$OVERFLOW", Overflowing::class.java.name)
        put("MessageDigest.$EXCEPTION", Excepting::class.java.name)
    }

    abstract class Armed : MessageDigestSpi() {
        private val inner = MessageDigest.getInstance("SHA-256", "SUN")
        override fun engineUpdate(input: Byte) = inner.update(input)
        override fun engineUpdate(input: ByteArray, offset: Int, len: Int) = inner.update(input, offset, len)
        override fun engineReset() = inner.reset()
        override fun engineDigest(): ByteArray {
            if (armed) fail()
            return inner.digest()
        }
        abstract fun fail()
    }

    class Asserting : Armed() {
        override fun fail() = throw AssertionError("armed")
    }

    class Overflowing : Armed() {
        override fun fail() {
            deep(0)
        }
        private fun deep(n: Int): Int = deep(n + 1) + 1
    }

    class Excepting : Armed() {
        override fun fail() = throw IllegalStateException("armed")
    }

    companion object {
        const val NAME = "Throwing"
        const val ASSERTION = "ASSERTION"
        const val OVERFLOW = "OVERFLOW"
        const val EXCEPTION = "EXCEPTION"

        @Volatile
        var armed = false
    }
}
