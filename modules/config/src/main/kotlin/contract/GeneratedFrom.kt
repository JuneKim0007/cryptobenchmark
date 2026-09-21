package io.github.junekim0007.cryptobench.config.contract

/** The environment files a configuration was generated from, so a file made on one device is recognisable on another. */
data class GeneratedFrom(
    val capture: String,
    val trial: String,
    val device: Map<String, Any>,
) {

    init {
        require(capture.isNotBlank()) { "missing_field: capture" }
        require(trial.isNotBlank()) { "missing_field: trial" }
    }
}
