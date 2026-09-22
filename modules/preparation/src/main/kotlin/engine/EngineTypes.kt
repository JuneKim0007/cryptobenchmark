package io.github.junekim0007.cryptobench.preparation.engine

import io.github.junekim0007.cryptobench.preparation.measurement.EngineTypeName
import io.github.junekim0007.cryptobench.preparation.measurement.Operation

class EngineTypes private constructor(
    private val types: Map<String, List<Operation>>,
    private val fallback: List<Operation>,
) {

    fun operationsOf(type: String): List<Operation> = types[EngineTypeName.fold(type)] ?: fallback

    fun with(type: String, operations: List<Operation>): EngineTypes =
        EngineTypes(types + (EngineTypeName.fold(type) to operations), fallback)

    companion object {

        fun standard(): EngineTypes = EngineTypes(
            types = mapOf(
                "Cipher" to listOf(Operation.ENCRYPT, Operation.DECRYPT),
                "Signature" to listOf(Operation.SIGN, Operation.VERIFY),
                "Mac" to listOf(Operation.COMPUTE_MAC),
                "MessageDigest" to listOf(Operation.DIGEST),
                "KeyGenerator" to listOf(Operation.GENERATE_KEY),
                "KeyPairGenerator" to listOf(Operation.GENERATE_KEY_PAIR),
                "KeyAgreement" to listOf(Operation.AGREE_KEY),
            ).mapKeys { (type, _) -> EngineTypeName.fold(type) },
            fallback = listOf(Operation.TYPE_DEFAULT),
        )
    }
}
