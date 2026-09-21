package io.github.junekim0007.cryptobench.preparation.parameter.bind

import java.security.spec.AlgorithmParameterSpec

/** A validated tree. `next()` builds the spec; when `varies`, each call has new random parts and must be made before the timer. */
class BoundParameters internal constructor(private val root: ValueNode) {

    val varies: Boolean get() = root.varies

    fun next(): AlgorithmParameterSpec = root.evaluate() as AlgorithmParameterSpec
}
