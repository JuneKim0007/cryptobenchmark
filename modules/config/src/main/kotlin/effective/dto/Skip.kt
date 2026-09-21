package io.github.junekim0007.cryptobench.config.effective.dto

data class Skip(
    val stage: String,
    val provider: String? = null,
    val type: String? = null,
    val name: String? = null,
    val reason: String,
) {

    init {
        require(stage.isNotBlank()) { "missing_field: stage" }
        require(reason.isNotBlank()) { "missing_field: reason" }
    }

    override fun toString(): String = "[$stage] ${provider ?: "*"} ${type ?: "*"} ${name ?: "*"}: $reason"

    companion object {
        const val CONFIG = "config"
    }
}
