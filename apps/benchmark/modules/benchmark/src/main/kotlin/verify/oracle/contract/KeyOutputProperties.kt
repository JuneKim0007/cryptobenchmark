package io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.ResolvedParameters
import java.security.KeyPair
import javax.crypto.SecretKey

/** Key generators: the output is a key of the asked kind, its size the case's key size where one was asked; a second call gives another key. */
internal class KeyOutputProperties(private val pair: Boolean) : Properties {

    override fun of(call: CheckedCall): Map<String, Outcome> {
        val output = call.output
        val kind = if (pair) output is KeyPair else output is SecretKey
        if (!kind) return mapOf("kind" to Outcome.Fail("not_a_key: ${output?.javaClass?.simpleName}"))
        val bits = ResolvedParameters.of(null, KeyMaterial.None, output)[ResolvedParameters.KEY_BITS] as? Int
        val asked = call.prepared.case.keySize
        val again = runCatching { call.invocation.once() }.getOrNull()
        val encoded = { key: Any? -> (if (key is KeyPair) key.private else key as? SecretKey)?.encoded }
        return linkedMapOf(
            "kind" to Outcome.Pass,
            "size" to if (asked == null || bits == null) Outcome.NotCheckable("no_size_asked_or_read") else holds(bits == asked) { "size: $bits bits, the case asked $asked" },
            "fresh" to holds(encoded(again) != null && !encoded(again).contentEquals(encoded(output))) { "fresh: a second call returned the same key" },
        )
    }
}
