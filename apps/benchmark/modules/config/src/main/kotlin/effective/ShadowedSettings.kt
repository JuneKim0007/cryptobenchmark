package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.global.dto.GlobalConfig
import io.github.junekim0007.cryptobench.config.testset.dto.TestSet
import io.github.junekim0007.cryptobench.settings.EnergySettings

/** Authored keys another key overrides: with run.passes no harness.iterations reaches a device case; a measured capture takes no energy cool-down. */
object ShadowedSettings {

    fun of(global: GlobalConfig, testSet: TestSet): List<String> = iterations(global, testSet) + energyCooldown(global, testSet)

    private fun iterations(global: GlobalConfig, testSet: TestSet): List<String> {
        if (global.run.passes.isEmpty()) return emptyList()
        val run = listOfNotNull("run.harness.iterations".takeIf { global.run.harness.iterations != null })
        val overrides = testSet.overrides.withIndex().filter { it.value.harness?.iterations != null }.map { "overrides[${it.index}].set.harness.iterations" }
        return (run + overrides).map { "shadowed_setting: $it is unused while run.passes sets the samples of a --device run" }
    }

    private fun energyCooldown(global: GlobalConfig, testSet: TestSet): List<String> {
        val runCapture = global.run.harness.energy.capture ?: EnergySettings.DEFAULTS.capture
        val anyDry = testSet.overrides.any { it.harness?.energy?.capture == DRY }
        val run = listOfNotNull("run.harness.energy.cooldownSeconds".takeIf {
            global.run.harness.energy.cooldownSeconds != null && runCapture == MEASURED && !anyDry
        })
        val overrides = testSet.overrides.withIndex().filter { (_, override) ->
            val energy = override.harness?.energy
            energy?.cooldownSeconds != null && (energy.capture ?: runCapture) == MEASURED
        }.map { "overrides[${it.index}].set.harness.energy.cooldownSeconds" }
        return (run + overrides).map { "shadowed_setting: $it is unused by a measured capture; the cool-down applies to dry only" }
    }

    private const val MEASURED = "measured"
    private const val DRY = "dry"
}
