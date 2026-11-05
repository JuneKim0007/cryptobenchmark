package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import io.github.junekim0007.cryptobench.discovery.trial.call.CipherCall
import java.security.InvalidKeyException
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

internal object CipherFacts : RequirementCall {

    private val INPUTS = listOf(0, 1, 2, 7, 8, 15, 16, 17, 31, 32, 33, 63, 64, 100, 1024)
    private const val MAX_INPUT_SEARCH = 1024

    override fun instance(service: ProbedService) {
        Cipher.getInstance(service.algorithm, service.provider)
    }

    override fun measure(service: ProbedService, sheet: FactSheet): CallResult {
        val engine = CipherEngine(service.provider, service.algorithm)
        val search = CipherBase.find(service, engine)
        val base = search.base ?: return CallResult(search.reason, search.detail, keysTried = search.tried)
        val key = base.key
        val message = base.message
        val like = base.like
        val runWith = linkedMapOf<String, Any>("operation" to if (base.wrapOnly) "wrap" else "encrypt", "providerGenerates" to base.providerGenerates)
        like?.let { runWith["spec"] = ParameterSpecs.describe(it) }
        if (!base.wrapOnly) runWith["inputBytes"] = message.size

        sheet.measure("defaultInit") { defaultInit(engine, base) }
        sheet.measure("blockBytes") { engine.encrypting(key.encrypting, ParameterSpecs.fresh(like)).blockSize }
        sheet.measure("specClasses") { specClasses(engine, base) }
        if (like != null) ParameterSpecs.ivOf(like)?.let { sheet.measure("ivBytes") { ivBytes(engine, base, like) } }
        if (like is GCMParameterSpec) sheet.measure("tagBits") { tagBits(engine, base, like) }
        if (key.isRawSecret) sheet.measure("keyBytes") { keyBytes(engine, base) }
        if (key.pair != null && service.keys.sizable(key)) sheet.measure("keyBits") { pairBits(service, engine, base) }
        sheet.measure("foreignKeys") { ForeignKeys.of(service, key) { other -> tryKey(engine, base, other) } }
        if (base.wrapOnly) {
            sheet.measure("wrapRoundTrip") { wrapRoundTrip(engine, base) }
            return CallResult(key = key, runWith = runWith, keysTried = search.tried)
        }
        sheet.measure("inputBytes") { inputBytes(engine, base) }
        sheet.measure("outputSize") { outputSize(engine, base) }
        sheet.measure("deterministicFixed") { deterministicFixed(engine, base) }
        sheet.measure("deterministicGenerated") { deterministicGenerated(engine, base) }
        sheet.measure("reuseGuard") { reuseGuard(engine, base) }
        sheet.measure("roundTrip") { roundTrip(engine, base) }
        sheet.measure("decryptWithoutParameters") { ErrorText.refusal { engine.create().init(Cipher.DECRYPT_MODE, key.decrypting) } ?: "ok" }
        sheet.measure("tamper") { tamper(engine, base) }
        sheet.measure("aad") { aad(engine, base) }
        sheet.measure("effects") { CipherEffects(service, engine, base).measure() }
        val fixed = ParameterSpecs.fresh(like)
        val ciphertext = engine.encrypt(key.encrypting, fixed, message)
        privateKeyRefused(engine, base, fixed, ciphertext)?.let {
            return CallResult(ServiceRequirement.KEY_REFUSED, it, key, runWith, search.tried)
        }
        return CallResult(
            key = key,
            runWith = runWith,
            keysTried = search.tried,
            aliasRuns = { alias -> check(CipherEngine(service.provider, alias).decrypt(key.decrypting, CipherEngine.Sent(fixed), ciphertext).contentEquals(message)) { "decrypts_differently" } },
            aliasAcceptsKey = { alias, other -> engine(service, alias).encrypt(other.encrypting, ParameterSpecs.fresh(like), message) },
        )
    }

    // Encrypting takes any public key; the private side decides whether a software key really runs here.
    private fun privateKeyRefused(engine: CipherEngine, base: CipherBase, fixed: AlgorithmParameterSpec?, ciphertext: ByteArray): String? {
        if (base.key.pair == null) return null
        val thrown = runCatching { engine.decrypt(base.key.decrypting, CipherEngine.Sent(fixed), ciphertext) }.exceptionOrNull()
        return if (thrown is InvalidKeyException) ErrorText.of(thrown) else null
    }

    private fun engine(service: ProbedService, name: String) = CipherEngine(service.provider, name)

    private fun tryKey(engine: CipherEngine, base: CipherBase, other: ProbeKey) {
        val cipher = engine.encrypting(other.encrypting, ParameterSpecs.fresh(base.like))
        if (!base.wrapOnly) cipher.doFinal(base.message)
    }

    private fun defaultInit(engine: CipherEngine, base: CipherBase): Map<String, Any> {
        val cipher = runCatching { engine.encrypting(base.key.encrypting, null) }
            .getOrElse { return mapOf("refused" to ErrorText.of(it)) }
        val out = linkedMapOf<String, Any>("accepted" to true)
        ParameterSpecs.generated(cipher)?.let { out["generated"] = ParameterSpecs.describe(it) }
        cipher.parameters?.let { out["parametersAlgorithm"] = it.algorithm }
        val first = cipher.iv
        out["providerChose"] = CipherCall.chosenParameters(cipher, base.key.encrypting)
        if (first != null) {
            out["ivRandomPerInit"] = !first.contentEquals(engine.encrypting(base.key.encrypting, null).iv)
        }
        return out
    }

    // Ignored: taken at init, yet two runs on that one spec differ, so the provider made its own parameters instead.
    private fun specClasses(engine: CipherEngine, base: CipherBase): Map<String, Any> {
        val accepted = ParameterSpecs.candidates().filter { (_, spec) ->
            ErrorText.refusal { if (base.wrapOnly) engine.encrypting(base.key.encrypting, spec) else engine.encrypt(base.key.encrypting, spec, base.message) } == null
        }
        val out = linkedMapOf<String, Any>("accepted" to accepted.map { it.first })
        if (!base.wrapOnly && deterministicFixed(engine, base)) {
            out["ignored"] = accepted.filter { (_, spec) ->
                !engine.encrypt(base.key.encrypting, spec, base.message).contentEquals(engine.encrypt(base.key.encrypting, spec, base.message))
            }.map { it.first }
        }
        return out
    }

    private fun ivBytes(engine: CipherEngine, base: CipherBase, like: AlgorithmParameterSpec): Map<String, Any> =
        Sweep.of(0..32) { engine.encrypt(base.key.encrypting, ParameterSpecs.withIv(like, ParameterSpecs.random(it)), base.message) }

    private fun tagBits(engine: CipherEngine, base: CipherBase, like: GCMParameterSpec): Map<String, Any> =
        Sweep.of(0..256 step 8) { engine.encrypt(base.key.encrypting, GCMParameterSpec(it, ParameterSpecs.random(like.iv.size)), base.message) }

    private fun keyBytes(engine: CipherEngine, base: CipherBase): Map<String, Any> =
        Sweep.of(1..64) {
            val cipher = engine.encrypting(SecretKeySpec(ParameterSpecs.random(it), base.key.encrypting.algorithm), ParameterSpecs.fresh(base.like))
            if (!base.wrapOnly) cipher.doFinal(base.message)
        }

    private fun pairBits(service: ProbedService, engine: CipherEngine, base: CipherBase): Map<String, Any> {
        val generator = service.keys.generatorOf(base.key) ?: return emptyMap()
        val out = linkedMapOf<String, Any>()
        for (bits in PairSizes.ALL) {
            val sized = service.keys.sized(base.key, bits, generator)
            out[bits.toString()] = sized.fold(
                onSuccess = { key -> if (base.wrapOnly) "ok" else ErrorText.refusal { engine.encrypt(key.encrypting, base.like, ByteArray(1)) } ?: "maxInput=${maxInput(engine, key, base)}" },
                onFailure = { "generation refused: " + ErrorText.of(it) },
            )
        }
        return out
    }

    private fun maxInput(engine: CipherEngine, key: ProbeKey, base: CipherBase): Int {
        var low = 0
        var high = MAX_INPUT_SEARCH
        while (low < high) {
            val middle = (low + high + 1) / 2
            if (ErrorText.refusal { engine.encrypt(key.encrypting, ParameterSpecs.fresh(base.like), ByteArray(middle)) } == null) low = middle else high = middle - 1
        }
        return low
    }

    private fun inputBytes(engine: CipherEngine, base: CipherBase): Map<String, Any> {
        val out = LinkedHashMap(Sweep.of(INPUTS) { engine.encrypt(base.key.encrypting, ParameterSpecs.fresh(base.like), ByteArray(it)) })
        if (base.key.pair != null) out["maxInputBytes"] = maxInput(engine, base.key, base)
        return out
    }

    private fun outputSize(engine: CipherEngine, base: CipherBase): Map<String, Any> {
        val rows = mutableListOf<String>()
        var exact = true
        for (size in INPUTS) {
            val cipher = engine.encrypting(base.key.encrypting, ParameterSpecs.fresh(base.like))
            val predicted = cipher.getOutputSize(size)
            val actual = runCatching { cipher.doFinal(ByteArray(size)).size }.getOrNull() ?: continue
            if (predicted != actual) exact = false
            rows += "$size:$predicted/$actual"
        }
        return linkedMapOf("predictedExactly" to exact, "inputPredictedActual" to rows.joinToString(" "))
    }

    private fun deterministicFixed(engine: CipherEngine, base: CipherBase): Boolean {
        val fixed = ParameterSpecs.fresh(base.like)
        return engine.encrypt(base.key.encrypting, fixed, base.message).contentEquals(engine.encrypt(base.key.encrypting, fixed, base.message))
    }

    private fun deterministicGenerated(engine: CipherEngine, base: CipherBase): Any =
        runCatching { engine.encrypt(base.key.encrypting, null, base.message).contentEquals(engine.encrypt(base.key.encrypting, null, base.message)) }
            .getOrElse { mapOf("refused" to ErrorText.of(it)) }

    private fun reuseGuard(engine: CipherEngine, base: CipherBase): Map<String, Any> {
        val fixed = ParameterSpecs.fresh(base.like)
        val cipher = engine.encrypting(base.key.encrypting, fixed)
        cipher.doFinal(base.message)
        val refused = ErrorText.refusal { CipherEngine.init(cipher, Cipher.ENCRYPT_MODE, base.key.encrypting, fixed) }
        return linkedMapOf<String, Any>("refused" to (refused != null)).apply { refused?.let { put("error", it) } }
    }

    private fun roundTrip(engine: CipherEngine, base: CipherBase): Boolean {
        val fixed = ParameterSpecs.fresh(base.like)
        val cipher = engine.encrypting(base.key.encrypting, fixed)
        val sent = CipherEngine.Sent(fixed, cipher.parameters)
        return engine.decrypt(base.key.decrypting, sent, cipher.doFinal(base.message)).contentEquals(base.message)
    }

    private fun tamper(engine: CipherEngine, base: CipherBase): String {
        val fixed = ParameterSpecs.fresh(base.like)
        val output = engine.encrypt(base.key.encrypting, fixed, base.message)
        if (output.isEmpty()) return "no output"
        output[output.size - 1] = (output[output.size - 1].toInt() xor 1).toByte()
        return runCatching { engine.decrypt(base.key.decrypting, CipherEngine.Sent(fixed), output) }.fold(
            onSuccess = { if (it.contentEquals(base.message)) "accepted, same plaintext" else "accepted, altered plaintext" },
            onFailure = { "refused " + it.javaClass.simpleName },
        )
    }

    private fun aad(engine: CipherEngine, base: CipherBase): Map<String, Any> {
        val cipher = engine.encrypting(base.key.encrypting, ParameterSpecs.fresh(base.like))
        val refused = ErrorText.refusal { cipher.updateAAD(ByteArray(16)) } ?: return aadBound(engine, base)
        return linkedMapOf("supported" to false, "error" to refused)
    }

    private fun aadBound(engine: CipherEngine, base: CipherBase): Map<String, Any> {
        val fixed = ParameterSpecs.fresh(base.like)
        val output = engine.encrypt(base.key.encrypting, fixed, base.message, ByteArray(16))
        return linkedMapOf(
            "supported" to true,
            "decryptWithoutAad" to (ErrorText.refusal { engine.decrypt(base.key.decrypting, CipherEngine.Sent(fixed), output) } ?: "ok"),
        )
    }

    private fun wrapRoundTrip(engine: CipherEngine, base: CipherBase): Map<String, Any> {
        val fixed = ParameterSpecs.fresh(base.like)
        val wrapped = SecretKeySpec(ParameterSpecs.random(16), base.key.algorithm)
        val cipher = engine.create()
        CipherEngine.init(cipher, Cipher.WRAP_MODE, base.key.encrypting, fixed)
        val bytes = cipher.wrap(wrapped)
        val back = engine.create()
        CipherEngine.init(back, Cipher.UNWRAP_MODE, base.key.decrypting, fixed)
        return linkedMapOf(
            "wrappedBytes" to bytes.size,
            "same" to back.unwrap(bytes, base.key.algorithm, Cipher.SECRET_KEY).encoded.contentEquals(wrapped.encoded),
        )
    }
}
