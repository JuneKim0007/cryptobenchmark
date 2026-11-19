package io.github.junekim0007.cryptobench.preparation.global

import io.github.junekim0007.cryptobench.settings.OnFailure
import io.github.junekim0007.cryptobench.settings.HarnessSettings

import io.github.junekim0007.cryptobench.preparation.inbound.InboundDocument
import io.github.junekim0007.cryptobench.settings.Metric
import io.github.junekim0007.cryptobench.settings.Phase
import io.github.junekim0007.cryptobench.settings.RunKeys
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.document.DocumentFields.choice
import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.numbers
import io.github.junekim0007.cryptobench.document.DocumentFields.sectionOrEmpty
import io.github.junekim0007.cryptobench.document.DocumentFields.string
import io.github.junekim0007.cryptobench.document.DocumentFields.strings

object GlobalReader {

    private val POLICY_KEYS = listOf("onFailure")

    fun read(inbound: InboundDocument): GlobalSettings {
        expectKeys(inbound.run, RunKeys.ALL, "run")
        expectKeys(inbound.policy, POLICY_KEYS, "policy")
        return settings(inbound)
    }

    private fun settings(inbound: InboundDocument) = GlobalSettings(
        inputSizes = numbers(inbound.run, RunKeys.INPUT_SIZES),
        phases = Phase.read(strings(inbound.run, RunKeys.PHASES), "run.phases"),
        metrics = Metric.read(strings(inbound.run, RunKeys.METRICS), "run.metrics"),
        processRepetitions = number(inbound.run, RunKeys.PROCESS_REPETITIONS).toInt(),
        seed = number(inbound.run, RunKeys.SEED).toLong(),
        onFailure = choice<OnFailure>("onFailure", string(inbound.policy, "onFailure")),
        harness = HarnessSettings.read(sectionOrEmpty(inbound.run, RunKeys.HARNESS), "run.harness"),
        variants = strings(inbound.run, RunKeys.VARIANTS).map(Variant::of),
    )
}
