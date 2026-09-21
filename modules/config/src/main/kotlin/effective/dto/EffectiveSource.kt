package io.github.junekim0007.cryptobench.config.effective.dto

/** Every file that went into an effective configuration, so a run can be traced back to its inputs. */
data class EffectiveSource(
    val global: String,
    val testSet: String,
    val inventory: String,
    val capture: String,
    val trial: String,
    val device: Map<String, Any>,
)
