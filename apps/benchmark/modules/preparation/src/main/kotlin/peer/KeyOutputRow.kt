package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.jca.peer.PeerPair
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import java.security.KeyPair
import java.security.KeyPairGenerator
import javax.crypto.SecretKey

/** A generated key is judged by use: the producer runs the key's catalogue use once with it, and the consumer takes that call through the use's row. */
internal object KeyOutputRow : PeerRow {

    override val mode = PeerEngine.PRODUCE_CONSUME

    override fun ready(produced: ProducedCall): Outcome? =
        if (produced.output is SecretKey || produced.output is KeyPair) null else Outcome.Fail("not_a_key: ${produced.output?.javaClass?.simpleName}")

    fun algorithm(key: Any?): String = if (key is KeyPair) key.public.algorithm else (key as SecretKey).algorithm

    // an agreement needs the other party's pair: the jca PeerPair on the generated key's curve or group
    fun used(produced: ProducedCall, use: KeyUse.Use): ProducedCall {
        val provider = produced.prepared.case.provider
        val key = when (val output = produced.output) {
            is KeyPair -> KeyMaterial.Pairs(if (use.operation == Operation.AGREE_KEY) listOf(output, PeerPair.of(output, KeyPairGenerator.getInstance(output.public.algorithm, provider))) else listOf(output))
            else -> KeyMaterial.Secret(output as SecretKey)
        }
        return ProducedCall.of(PeerCase.of(use.type, use.algorithm, provider, use.operation, null, null), KeyRecipe.None, key)
    }
}
