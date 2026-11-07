package io.github.junekim0007.cryptobench.preparation.parameter.bind

import java.security.spec.AlgorithmParameterSpec

class BoundParameters internal constructor(private val root: ValueNode) {

    val varies: Boolean get() = root.varies

    fun next(): AlgorithmParameterSpec = root.evaluate() as AlgorithmParameterSpec

    companion object {

        // The end-to-end check's fixed values: these specs in turn, never a fresh draw.
        fun cycling(specs: List<AlgorithmParameterSpec>): BoundParameters = BoundParameters(ValueNode.Cycle(specs))
    }
}
