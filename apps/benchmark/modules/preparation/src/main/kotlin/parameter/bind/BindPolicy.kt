package io.github.junekim0007.cryptobench.preparation.parameter.bind

import java.math.BigInteger
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.spec.PSource

class BindPolicy(private val allowed: List<Class<*>>) {

    fun permits(type: Class<*>): Boolean = allowed.any { it.isAssignableFrom(type) }

    fun describe(): String = allowed.joinToString { it.name }

    companion object {

        fun standard(): BindPolicy = BindPolicy(listOf(AlgorithmParameterSpec::class.java, PSource::class.java, BigInteger::class.java))
    }
}
