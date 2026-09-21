package io.github.junekim0007.cryptobench.config.generate

import io.github.junekim0007.cryptobench.config.contract.BenchmarkConfig
import io.github.junekim0007.cryptobench.config.contract.ConfigEntry
import io.github.junekim0007.cryptobench.config.contract.GeneratedFrom
import io.github.junekim0007.cryptobench.config.contract.RunSettings
import io.github.junekim0007.cryptobench.config.source.CaptureView
import io.github.junekim0007.cryptobench.config.source.TrialView

/** Capture × trial → default configuration: every name with a default run, enabled exactly when it ran. */
class DefaultConfigBuilder(private val run: RunSettings = RunDefaults.standard()) {

    fun build(capture: CaptureView, trial: TrialView): BenchmarkConfig {
        require(capture.capturedAtMillis == trial.capturedAtMillis) {
            "mismatched_trial: capture ${capture.capturedAtMillis}, trial ${trial.capturedAtMillis}"
        }
        val order = capture.providers + trial.entries.map { it.provider }.distinct().filter { it !in capture.providers }
        val byProvider = trial.entries.groupBy { it.provider }
        val providers = LinkedHashMap<String, Map<String, Map<String, ConfigEntry>>>()
        for (provider in order) {
            val entries = byProvider[provider] ?: continue
            val types = LinkedHashMap<String, LinkedHashMap<String, ConfigEntry>>()
            for (entry in entries) {
                types.getOrPut(entry.type) { LinkedHashMap() }[entry.name] = configEntry(entry.run)
            }
            providers[provider] = types
        }
        return BenchmarkConfig(GeneratedFrom(capture.fileName, trial.fileName, capture.device), run, providers)
    }

    private fun configEntry(defaultRun: TrialView.DefaultRun): ConfigEntry = ConfigEntry(
        enabled = defaultRun.works,
        keySizes = listOfNotNull(defaultRun.keySize),
        inputSizes = listOfNotNull(defaultRun.inputSize?.takeIf { it !in run.inputSizes }),
        keyAlgorithm = defaultRun.keyAlgorithm,
        keyProvider = defaultRun.keyProvider,
        providerChose = defaultRun.providerChose,
        bareName = defaultRun.bareName,
        reason = defaultRun.error,
    )
}
