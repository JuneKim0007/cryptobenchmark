package io.github.junekim0007.cryptobench.preparation.global

import io.github.junekim0007.cryptobench.settings.HarnessSettings

import io.github.junekim0007.cryptobench.preparation.inbound.InboundDocument
import io.github.junekim0007.cryptobench.settings.Metric
import io.github.junekim0007.cryptobench.preparation.measurement.Phase
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.choice
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.number
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.numbers
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.string
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.strings

object GlobalReader {

    fun read(inbound: InboundDocument): GlobalSettings = GlobalSettings(
        inputSizes = numbers(inbound.run, "inputSizes"),
        phases = strings(inbound.run, "phases").mapTo(LinkedHashSet()) { choice<Phase>("phase", it) },
        metrics = Metric.read(strings(inbound.run, "metrics"), "run.metrics"),
        processRepetitions = number(inbound.run, "processRepetitions").toInt(),
        seed = number(inbound.run, "seed").toLong(),
        onFailure = choice<OnFailure>("onFailure", string(inbound.policy, "onFailure")),
        harness = HarnessSettings.read(optionalSection(inbound.run, "harness"), "run.harness"),
        variants = optionalStrings(inbound.run, "variants").map(Variant::of).ifEmpty { Variant.entries },
    )
}
