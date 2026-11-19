package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.global.dto.GlobalConfig
import io.github.junekim0007.cryptobench.config.testset.dto.TestSet

/** Authored keys another key overrides: with run.passes every pass sends its samples, so no harness.iterations reaches a device case. */
object ShadowedSettings {

    fun of(global: GlobalConfig, testSet: TestSet): List<String> {
        if (global.run.passes.isEmpty()) return emptyList()
        val run = listOfNotNull("run.harness.iterations".takeIf { global.run.harness.iterations != null })
        val overrides = testSet.overrides.withIndex().filter { it.value.harness?.iterations != null }.map { "overrides[${it.index}].set.harness.iterations" }
        return (run + overrides).map { "shadowed_setting: $it is unused while run.passes sets the samples of a --device run" }
    }
}
