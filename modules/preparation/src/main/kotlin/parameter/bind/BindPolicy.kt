package io.github.junekim0007.cryptobench.preparation.parameter.bind

import java.math.BigInteger
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.spec.PSource

/**
 * Which classes a configuration may name. The file is user-edited and binding runs constructors, so anything
 * outside parameter-spec types is refused before a class is initialised or a constructor runs.
 */
class BindPolicy(private val allowed: List<Class<*>>) {

    fun permits(type: Class<*>): Boolean = allowed.any { it.isAssignableFrom(type) }

    fun describe(): String = allowed.joinToString { it.name }

    companion object {

        fun standard(): BindPolicy = BindPolicy(listOf(AlgorithmParameterSpec::class.java, PSource::class.java, BigInteger::class.java))
    }
}
