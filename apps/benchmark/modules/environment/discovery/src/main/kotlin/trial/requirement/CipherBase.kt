package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.Attempt
import io.github.junekim0007.cryptobench.discovery.contract.ErrorText
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import java.security.InvalidKeyException
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher
import javax.crypto.spec.SecretKeySpec

// The first key, spec and input the service runs on; every other fact varies one argument from here.
internal class CipherBase private constructor(
    val key: ProbeKey,
    val like: AlgorithmParameterSpec?,
    val providerGenerates: Boolean,
    val message: ByteArray,
    val wrapOnly: Boolean,
) {

    class Search(val base: CipherBase?, val reason: String, val detail: String, val tried: List<Map<String, Any>>)

    /** The secret every wrap fact wraps: fresh bytes under the base key's algorithm. */
    fun toWrap(): SecretKeySpec = toWrap(key)

    companion object {

        private val MESSAGE_SIZES = listOf(64, 32, 16, 8, 1, 0)

        private const val WRAPPED_BYTES = 16

        private fun toWrap(key: ProbeKey) = SecretKeySpec(ParameterSpecs.random(WRAPPED_BYTES), key.algorithm)

        fun find(service: ProbedService, engine: CipherEngine): Search {
            val tried = mutableListOf<Map<String, Any>>()
            var keyAccepted = false
            var firstDetail = ""
            for (key in service.keys.of(service.type, service.algorithm, service.provider)) {
                val specs = listOf<Pair<String, AlgorithmParameterSpec?>>("" to null) + ParameterSpecs.candidates()
                var refusedOtherThanKey: String? = null
                for ((_, spec) in specs) {
                    runnable(engine, key, spec)?.let { return Search(it, "", "", tried) }
                    val initRefused = Attempt.of { engine.encrypting(key.encrypting, spec) }.exceptionOrNull()
                    if (initRefused == null) {
                        keyAccepted = true
                        continue
                    }
                    if (initRefused !is InvalidKeyException && refusedOtherThanKey == null) refusedOtherThanKey = ErrorText.of(initRefused)
                    if (firstDetail.isEmpty()) firstDetail = ErrorText.of(initRefused)
                }
                tried += key.describe() + ("refused" to (refusedOtherThanKey ?: firstDetail))
            }
            val reason = when {
                tried.isEmpty() -> ServiceRequirement.NO_KEY
                keyAccepted -> ServiceRequirement.OPERATION_REFUSED
                tried.all { (it["refused"] as String).startsWith(InvalidKeyException::class.java.simpleName) } -> ServiceRequirement.KEY_REFUSED
                else -> ServiceRequirement.PARAMETERS_UNKNOWN
            }
            return Search(null, reason, firstDetail, tried)
        }

        private fun runnable(engine: CipherEngine, key: ProbeKey, spec: AlgorithmParameterSpec?): CipherBase? {
            for (size in MESSAGE_SIZES) {
                val message = ParameterSpecs.random(size)
                val works = Attempt.of { engine.encrypt(key.encrypting, ParameterSpecs.fresh(spec), message) }.isSuccess
                if (works) return of(engine, key, spec, message, wrapOnly = false)
            }
            val wraps = Attempt.of {
                val cipher = engine.create()
                CipherEngine.init(cipher, Cipher.WRAP_MODE, key.encrypting, ParameterSpecs.fresh(spec))
                cipher.wrap(toWrap(key))
            }.isSuccess
            return if (wraps) of(engine, key, spec, ByteArray(0), wrapOnly = true) else null
        }

        private fun of(engine: CipherEngine, key: ProbeKey, spec: AlgorithmParameterSpec?, message: ByteArray, wrapOnly: Boolean): CipherBase {
            val like = spec ?: if (wrapOnly) null else ParameterSpecs.generated(engine.encrypting(key.encrypting, null))
            return CipherBase(key, like, spec == null && like != null, message, wrapOnly)
        }
    }
}
