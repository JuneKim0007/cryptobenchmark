package io.github.junekim0007.cryptobench.preparation.engine

import io.github.junekim0007.cryptobench.preparation.measurement.EngineTypeName
import io.github.junekim0007.cryptobench.preparation.measurement.Operation

class EngineTypes private constructor(
    private val types: Map<String, EngineType>,
    private val fallback: EngineType,
) {

    fun of(type: String): EngineType = types[EngineTypeName.fold(type)] ?: fallback

    fun with(type: String, engineType: EngineType): EngineTypes = EngineTypes(types + (EngineTypeName.fold(type) to engineType), fallback)

    companion object {

        fun standard(): EngineTypes = EngineTypes(
            types = mapOf(
                "Cipher" to EngineType(listOf(Operation.ENCRYPT, Operation.DECRYPT), usesKeySize = true, usesInputSize = true, keyShape = KeyShape.DEVICE_DECIDES),
                "Signature" to EngineType(listOf(Operation.SIGN, Operation.VERIFY), usesKeySize = true, usesInputSize = true, keyShape = KeyShape.PAIR),
                "Mac" to EngineType(listOf(Operation.COMPUTE_MAC), usesKeySize = true, usesInputSize = true, keyShape = KeyShape.SECRET),
                "MessageDigest" to EngineType(listOf(Operation.DIGEST), usesKeySize = false, usesInputSize = true, keyShape = KeyShape.NONE),
                "KeyGenerator" to EngineType(listOf(Operation.GENERATE_KEY), usesKeySize = true, usesInputSize = false, keyShape = KeyShape.NONE),
                "KeyPairGenerator" to EngineType(listOf(Operation.GENERATE_KEY_PAIR), usesKeySize = true, usesInputSize = false, keyShape = KeyShape.NONE),
                "KeyAgreement" to EngineType(listOf(Operation.AGREE_KEY), usesKeySize = true, usesInputSize = false, keyShape = KeyShape.PEER_PAIRS),
                "SecureRandom" to EngineType(listOf(Operation.TYPE_DEFAULT), usesKeySize = true, usesInputSize = true, keyShape = KeyShape.NONE),
            ).mapKeys { (type, _) -> EngineTypeName.fold(type) },
            fallback = EngineType(listOf(Operation.TYPE_DEFAULT), usesKeySize = true, usesInputSize = true, keyShape = KeyShape.DEVICE_DECIDES),
        )
    }
}
