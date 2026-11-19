package io.github.junekim0007.cryptobench.preparation.interop

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.interop.plan.InteropPair
import io.github.junekim0007.cryptobench.preparation.interop.plan.Member
import io.github.junekim0007.cryptobench.preparation.interop.report.InteropVerdict
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.peer.Consumer
import io.github.junekim0007.cryptobench.preparation.peer.Outcome
import io.github.junekim0007.cryptobench.preparation.peer.PeerCase
import io.github.junekim0007.cryptobench.preparation.peer.PeerEngine
import io.github.junekim0007.cryptobench.preparation.peer.Travel
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.shared.FailureText

/** Each direction of a pair: the first member's provider produces the type's first operation once with one planned key, the other member consumes it through the peer engine; only message-borne parameters travel. */
class InteropOracle(
    private val capability: DeviceCapability,
    private val engineTypes: EngineTypes = EngineTypes.standard(),
    private val planner: KeyPlanner = KeyPlanner(capability, anyProvider = true),
    private val generator: KeyMaterialGenerator = KeyMaterialGenerator(),
) {

    private val engine = PeerEngine(capability)

    fun check(pair: InteropPair): InteropVerdict {
        val missing = listOf(pair.a, pair.b).mapNotNull { m ->
            (capability.check(m.provider, m.type, m.algorithm) as? Availability.Unavailable)?.let { "$m: ${it.reason}" }
        }
        if (missing.isNotEmpty()) {
            val out = Outcome.NotCheckable("not_registered: ${missing.joinToString()}")
            return InteropVerdict(pair, PeerEngine.NONE, out, out)
        }
        val operation = engineTypes.operationsOf(pair.a.type).first()
        return InteropVerdict(pair, PeerEngine.modeOf(operation), direction(pair.a, pair.b, operation, pair), direction(pair.b, pair.a, operation, pair))
    }

    private fun direction(producer: Member, consumer: Member, operation: Operation, pair: InteropPair): Outcome {
        val case = PeerCase.of(producer.type, producer.algorithm, producer.provider, operation, pair.keySize, pair.inputSize)
        val recipe = planner.plan(case)
        if (recipe is KeyRecipe.Unavailable) return Outcome.NotCheckable("no_key: ${recipe.reason}")
        val key = Attempt.of { generator.generate(recipe) }
            .getOrElse { return Outcome.NotCheckable(FailureText.of(it, "key_generation_failed: ")) }
        return engine.produced(case, recipe, key, Consumer(consumer.provider, consumer.algorithm), Travel.MESSAGE_BORNE)
    }
}
