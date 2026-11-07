package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ParameterReadBack
import java.security.SecureRandom
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PBEParameterSpec
import javax.crypto.spec.PSource

// Every variation is built from a spec a provider accepted, so no algorithm is named here; reading a spec back is ParameterReadBack.
internal object ParameterSpecs {

    private val RANDOM = SecureRandom()

    fun candidates(): List<Pair<String, AlgorithmParameterSpec>> = listOfNotNull(
        "IvParameterSpec(16)" to IvParameterSpec(random(16)),
        "IvParameterSpec(12)" to IvParameterSpec(random(12)),
        "IvParameterSpec(8)" to IvParameterSpec(random(8)),
        "GCMParameterSpec(128,12)" to GCMParameterSpec(128, random(12)),
        chaCha(random(12), 1)?.let { "ChaCha20ParameterSpec(12,1)" to it },
        "OAEPParameterSpec.DEFAULT" to OAEPParameterSpec.DEFAULT,
        "PBEParameterSpec(16,1000,iv16)" to PBEParameterSpec(random(16), 1000, IvParameterSpec(random(16))),
        "PBEParameterSpec(16,1000)" to PBEParameterSpec(random(16), 1000),
        "PBEParameterSpec(8,1000)" to PBEParameterSpec(random(8), 1000),
        "PSSParameterSpec.DEFAULT" to PSSParameterSpec.DEFAULT,
    )

    fun generated(cipher: Cipher): AlgorithmParameterSpec? =
        cipher.parameters?.let { ParameterReadBack.readable(it) } ?: cipher.iv?.let { IvParameterSpec(it) }

    fun ivOf(spec: AlgorithmParameterSpec?): ByteArray? = when {
        spec is GCMParameterSpec -> spec.iv
        spec is IvParameterSpec -> spec.iv
        spec is PBEParameterSpec -> (spec.parameterSpec as? IvParameterSpec)?.iv
        spec != null && ParameterReadBack.isChaCha(spec) -> ParameterReadBack.chaChaNonce(spec)
        else -> null
    }

    fun withIv(spec: AlgorithmParameterSpec, iv: ByteArray): AlgorithmParameterSpec = when {
        spec is GCMParameterSpec -> GCMParameterSpec(spec.tLen, iv)
        spec is PBEParameterSpec -> PBEParameterSpec(spec.salt, spec.iterationCount, IvParameterSpec(iv))
        ParameterReadBack.isChaCha(spec) -> chaCha(iv, ParameterReadBack.chaChaCounter(spec))!!
        else -> IvParameterSpec(iv)
    }

    // A new IV of the same length, so a reuse guard never answers for another fact.
    fun fresh(spec: AlgorithmParameterSpec?): AlgorithmParameterSpec? {
        val iv = ivOf(spec) ?: return spec
        return withIv(spec!!, random(iv.size))
    }

    fun oaep(digest: String, mgf1: String, label: ByteArray): OAEPParameterSpec =
        OAEPParameterSpec(digest, OAEPParameterSpec.DEFAULT.mgfAlgorithm, MGF1ParameterSpec(mgf1), PSource.PSpecified(label))

    fun random(length: Int): ByteArray = ByteArray(length).also { RANDOM.nextBytes(it) }

    private fun chaCha(nonce: ByteArray, counter: Int): AlgorithmParameterSpec? =
        ParameterReadBack.CHACHA?.getConstructor(ByteArray::class.java, Int::class.javaPrimitiveType)?.newInstance(nonce, counter) as AlgorithmParameterSpec?
}
