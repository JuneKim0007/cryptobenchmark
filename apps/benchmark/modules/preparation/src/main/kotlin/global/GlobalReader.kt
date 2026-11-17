package io.github.junekim0007.cryptobench.preparation.global

import io.github.junekim0007.cryptobench.settings.HarnessSettings

import io.github.junekim0007.cryptobench.preparation.inbound.InboundDocument
import io.github.junekim0007.cryptobench.settings.Metric
import io.github.junekim0007.cryptobench.preparation.measurement.Phase
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.document.DocumentFields.choice
import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.numbers
import io.github.junekim0007.cryptobench.document.DocumentFields.sectionOrEmpty
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.document.DocumentFields.string
import io.github.junekim0007.cryptobench.document.DocumentFields.strings

object GlobalReader {

    // Host-only keys (isolation, passes, warmup, ...) are known here but read by the runner.
    private val RUN_KEYS = listOf(
        "inputSizes", "phases", "metrics", "variants", "processRepetitions", "isolation", "seed", "passes",
        "thermalThrottleSleepSeconds", "caseCooldownSeconds", "warmup", "thermalGate", "launchRetries", "resumeBlockRuns", "harness",
    )
    private val POLICY_KEYS = listOf("onFailure")

    fun read(inbound: InboundDocument): GlobalSettings {
        expectKeys(inbound.run, RUN_KEYS, "run")
        expectKeys(inbound.policy, POLICY_KEYS, "policy")
        return settings(inbound)
    }

    private fun settings(inbound: InboundDocument) = GlobalSettings(
        inputSizes = numbers(inbound.run, "inputSizes"),
        phases = strings(inbound.run, "phases").mapTo(LinkedHashSet()) { choice<Phase>("phase", it) },
        metrics = Metric.read(strings(inbound.run, "metrics"), "run.metrics"),
        processRepetitions = number(inbound.run, "processRepetitions").toInt(),
        seed = number(inbound.run, "seed").toLong(),
        onFailure = choice<OnFailure>("onFailure", string(inbound.policy, "onFailure")),
        harness = HarnessSettings.read(sectionOrEmpty(inbound.run, "harness"), "run.harness"),
        variants = if ("variants" in inbound.run) optionalStrings(inbound.run, "variants").map(Variant::of) else Variant.entries,
    )
}
