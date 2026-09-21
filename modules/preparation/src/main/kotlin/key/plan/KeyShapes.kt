package io.github.junekim0007.cryptobench.preparation.key.plan

import io.github.junekim0007.cryptobench.preparation.measurement.EngineTypeName

/** Engine type → the key it is measured with. Types not registered let the device decide. */
class KeyShapes private constructor(private val shapes: Map<String, KeyShape>) {

    fun of(type: String): KeyShape = shapes[EngineTypeName.fold(type)] ?: KeyShape.DEVICE_DECIDES

    fun with(type: String, shape: KeyShape): KeyShapes = KeyShapes(shapes + (EngineTypeName.fold(type) to shape))

    companion object {

        fun standard(): KeyShapes = KeyShapes(
            mapOf(
                "MessageDigest" to KeyShape.NONE,
                "KeyGenerator" to KeyShape.NONE,
                "KeyPairGenerator" to KeyShape.NONE,
                "SecureRandom" to KeyShape.NONE,
                "Mac" to KeyShape.SECRET,
                "Signature" to KeyShape.PAIR,
                "KeyAgreement" to KeyShape.PEER_PAIRS,
                "Cipher" to KeyShape.DEVICE_DECIDES,
            ).mapKeys { (type, _) -> EngineTypeName.fold(type) },
        )
    }
}
