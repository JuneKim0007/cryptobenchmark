package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.jca.failure.ErrorText
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.MGF1ParameterSpec
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PBEParameterSpec

// Which optional argument changes the output: vary it alone. Only this finds an argument accepted and then ignored.
internal class CipherEffects(private val service: ProbedService, private val engine: CipherEngine, private val base: CipherBase) {

    fun measure(): Map<String, Any> {
        val like = base.like
        val fixed = ParameterSpecs.fresh(like)
        val out = linkedMapOf<String, Any>()
        val baseline = engine.encrypt(base.key.encrypting, fixed, base.message)
        for ((name, varied) in variants(fixed)) {
            out[name] = effect(baseline, fixed, varied, null)
        }
        if (ErrorText.refusal { engine.encrypting(base.key.encrypting, ParameterSpecs.fresh(like)).updateAAD(ByteArray(1)) } == null) {
            out["aad"] = effect(baseline, fixed, fixed, ByteArray(16))
        }
        return out
    }

    private fun effect(baseline: ByteArray, fixed: AlgorithmParameterSpec?, varied: AlgorithmParameterSpec?, aad: ByteArray?): Map<String, Any> {
        val output = Attempt.of { engine.encrypt(base.key.encrypting, varied, base.message, aad) }
            .getOrElse { return mapOf("refused" to ErrorText.of(it)) }
        val underBase = ErrorText.refusal {
            check(engine.decrypt(base.key.decrypting, CipherEngine.Sent(fixed), output).contentEquals(base.message)) { "wrong plaintext" }
        }
        return linkedMapOf(
            "outputChanged" to !output.contentEquals(baseline),
            "lengthDelta" to output.size - baseline.size,
            "decryptsUnderBase" to (underBase ?: "ok"),
        )
    }

    private fun variants(spec: AlgorithmParameterSpec?): List<Pair<String, AlgorithmParameterSpec>> = when (spec) {
        is GCMParameterSpec -> listOf(
            "ivBytesChanged" to GCMParameterSpec(spec.tLen, flipped(spec.iv)),
            "tagBitsChanged" to GCMParameterSpec(if (spec.tLen == OTHER_TAG_BITS) spec.tLen - TAG_STEP else OTHER_TAG_BITS, spec.iv),
            "ivLengthChanged" to GCMParameterSpec(spec.tLen, ParameterSpecs.random(spec.iv.size + IV_STEP)),
        )
        is IvParameterSpec -> listOf("ivBytesChanged" to IvParameterSpec(flipped(spec.iv)), "ivLengthChanged" to IvParameterSpec(spec.iv.copyOf(spec.iv.size / 2)))
        is OAEPParameterSpec -> oaepVariants(spec)
        is PBEParameterSpec -> listOfNotNull(
            "saltChanged" to PBEParameterSpec(flipped(spec.salt), spec.iterationCount, spec.parameterSpec),
            "iterationsChanged" to PBEParameterSpec(spec.salt, spec.iterationCount + 1, spec.parameterSpec),
            (spec.parameterSpec as? IvParameterSpec)?.let { "innerIvChanged" to PBEParameterSpec(spec.salt, spec.iterationCount, IvParameterSpec(flipped(it.iv))) },
        )
        null -> emptyList()
        else -> ParameterSpecs.ivOf(spec)?.let { listOf("ivBytesChanged" to ParameterSpecs.withIv(spec, flipped(it))) }.orEmpty()
    }

    private fun oaepVariants(spec: OAEPParameterSpec): List<Pair<String, AlgorithmParameterSpec>> {
        val mgf1 = (spec.mgfParameters as? MGF1ParameterSpec)?.digestAlgorithm ?: spec.digestAlgorithm
        val otherDigest = service.digests.firstOrNull { !it.equals(spec.digestAlgorithm, ignoreCase = true) && accepted(ParameterSpecs.oaep(it, mgf1, ByteArray(0))) }
        val otherMgf1 = service.digests.firstOrNull { !it.equals(mgf1, ignoreCase = true) && accepted(ParameterSpecs.oaep(spec.digestAlgorithm, it, ByteArray(0))) }
        return listOfNotNull(
            otherDigest?.let { "digestChanged" to ParameterSpecs.oaep(it, mgf1, ByteArray(0)) },
            otherMgf1?.let { "mgf1Changed" to ParameterSpecs.oaep(spec.digestAlgorithm, it, ByteArray(0)) },
            "labelChanged" to ParameterSpecs.oaep(spec.digestAlgorithm, mgf1, ByteArray(LABEL_BYTES)),
        )
    }

    private fun accepted(spec: OAEPParameterSpec): Boolean =
        ErrorText.refusal { engine.encrypting(base.key.encrypting, spec) } == null

    private fun flipped(bytes: ByteArray): ByteArray = bytes.clone().also { if (it.isNotEmpty()) it[0] = (it[0].toInt() xor 1).toByte() }

    private companion object {
        const val OTHER_TAG_BITS = 96
        const val TAG_STEP = 8
        const val IV_STEP = 4
        const val LABEL_BYTES = 4
    }
}
