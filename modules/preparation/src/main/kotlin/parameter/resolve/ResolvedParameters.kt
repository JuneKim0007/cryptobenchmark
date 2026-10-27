package io.github.junekim0007.cryptobench.preparation.parameter.resolve

import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import java.security.Key
import java.security.KeyPair
import java.security.Signature
import javax.crypto.Cipher

/** What the provider used for a case after its one call: read back from the engine, its reported parameters and the key. */
object ResolvedParameters {

    const val MODE = "mode"
    const val PADDING = "padding"
    const val IV_BYTES = "ivBytes"
    const val TAG_BITS = "tagBits"
    const val DIGEST = "digest"
    const val MGF1 = "mgf1"
    const val LABEL_BYTES = "labelBytes"
    const val KEY_BITS = "keyBits"
    const val CURVE = "curve"

    val KEYS = listOf(MODE, PADDING, IV_BYTES, TAG_BITS, DIGEST, MGF1, LABEL_BYTES, KEY_BITS, CURVE)

    fun of(engine: Any?, material: KeyMaterial, result: Any?): Map<String, Any> {
        val fields = HashMap<String, Any>()
        when (engine) {
            is Cipher -> fields.putAll(cipher(engine, material))
            is Signature -> fields.putAll(SpecFields.of(signatureParameters(engine)).fields)
        }
        fields.putAll(KeyFields.of(keyOf(material, result)))
        return KEYS.filter { it in fields }.associateWithTo(LinkedHashMap()) { fields.getValue(it) }
    }

    private fun cipher(cipher: Cipher, material: KeyMaterial): Map<String, Any> {
        val fields = LinkedHashMap<String, Any>()
        val parts = cipher.algorithm.split('/')
        if (parts.size == 3) {
            fields[MODE] = parts[1]
            fields[PADDING] = parts[2]
        }
        val reported = SpecFields.of(cipher.parameters)
        fields.putAll(reported.fields)
        if (IV_BYTES !in fields) {
            val candidate = reported.ivCandidate ?: cipher.iv?.size
            if (candidate != null && PerInitValue.isIv(cipher, CipherKeys.encrypting(material))) fields[IV_BYTES] = candidate
        }
        return fields
    }

    // Signature.getParameters is optional in the JCA contract; an engine without it reports nothing.
    private fun signatureParameters(signature: Signature) = try {
        signature.parameters
    } catch (unsupported: UnsupportedOperationException) {
        null
    }

    private fun keyOf(material: KeyMaterial, result: Any?): Key? = when (result) {
        is Key -> result
        is KeyPair -> result.public
        else -> when (material) {
            is KeyMaterial.Secret -> material.key
            is KeyMaterial.Pairs -> material.pairs.first().public
            KeyMaterial.None -> null
        }
    }
}
