package io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import java.security.MessageDigest
import javax.crypto.Mac

/** Digest and Mac: the length the engine declares, and the same output from a second call (the engine reset). */
internal class DigestProperties(private val declaredLength: (CheckedCall) -> Int) : Properties {

    override fun of(call: CheckedCall): Map<String, Outcome> {
        val output = call.output as? ByteArray ?: return mapOf("output" to Outcome.Fail("not_bytes: ${call.output?.javaClass?.simpleName}"))
        val declared = runCatching { declaredLength(call) }.getOrDefault(0)
        val again = runCatching { call.invocation.once() as? ByteArray }.getOrNull()
        return linkedMapOf(
            "length" to if (declared <= 0) Outcome.NotCheckable("no_declared_length") else holds(output.size == declared) { "length: ${output.size} bytes, the engine declares $declared" },
            "repeat" to holds(again?.contentEquals(output) == true) { "repeat_differs: a second call returned other bytes" },
        )
    }

    companion object {
        val DIGEST = DigestProperties { MessageDigest.getInstance(it.prepared.case.algorithm, it.prepared.case.provider).digestLength }
        val MAC = DigestProperties { Mac.getInstance(it.prepared.case.algorithm, it.prepared.case.provider).macLength }
    }
}
