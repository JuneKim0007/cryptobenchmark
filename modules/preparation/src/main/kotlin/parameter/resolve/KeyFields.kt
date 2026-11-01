package io.github.junekim0007.cryptobench.preparation.parameter.resolve

import io.github.junekim0007.cryptobench.preparation.record.Fingerprint
import java.security.AlgorithmParameters
import java.security.GeneralSecurityException
import java.security.Key
import java.security.interfaces.DSAKey
import java.security.interfaces.ECKey
import java.security.interfaces.RSAKey
import java.security.spec.ECFieldF2m
import java.security.spec.ECFieldFp
import java.security.spec.ECGenParameterSpec
import java.security.spec.ECParameterSpec
import javax.crypto.SecretKey
import javax.crypto.interfaces.DHKey

/** keyBits and curve of the key a case used, read by key interface. */
internal object KeyFields {

    fun of(key: Key?): Map<String, Any> {
        val fields = LinkedHashMap<String, Any>()
        bits(key)?.let { fields[ResolvedParameters.KEY_BITS] = it }
        (key as? ECKey)?.let { fields[ResolvedParameters.CURVE] = curve(it.params, key.algorithm) }
        return fields
    }

    private fun bits(key: Key?): Int? = when (key) {
        is SecretKey -> key.encoded?.let { it.size * Byte.SIZE_BITS }
        is RSAKey -> key.modulus.bitLength()
        is ECKey -> key.params.curve.field.fieldSize
        is DSAKey -> key.params?.p?.bitLength()
        is DHKey -> key.params.p.bitLength()
        else -> null
    }

    // The name comes from whichever AlgorithmParameters serves the key's algorithm; a curve it cannot name gets a hash.
    fun curve(spec: ECParameterSpec, keyAlgorithm: String): String = try {
        AlgorithmParameters.getInstance(keyAlgorithm).apply { init(spec) }.getParameterSpec(ECGenParameterSpec::class.java).name
    } catch (unnamed: GeneralSecurityException) {
        "field${spec.curve.field.fieldSize}-${hash(spec)}"
    }

    private fun hash(spec: ECParameterSpec): String {
        val field = when (val f = spec.curve.field) {
            is ECFieldFp -> "p=${f.p.toString(16)}"
            is ECFieldF2m -> "m=${f.m} r=${f.reductionPolynomial?.toString(16)}"
            else -> "field=${f.fieldSize}"
        }
        val text = "$field a=${spec.curve.a.toString(16)} b=${spec.curve.b.toString(16)} " +
            "gx=${spec.generator.affineX.toString(16)} gy=${spec.generator.affineY.toString(16)} n=${spec.order.toString(16)} h=${spec.cofactor}"
        return Fingerprint.of(text)
    }
}
