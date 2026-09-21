package io.github.junekim0007.cryptobench.config.effective.dto

/** Something the test set asked for that will not run, and why; a rule that matched nothing has no provider. */
data class Skip(
    val provider: String? = null,
    val type: String? = null,
    val name: String? = null,
    val reason: String,
) {

    init {
        require(reason.isNotBlank()) { "missing_field: reason" }
    }

    override fun toString(): String = "${provider ?: "*"} ${type ?: "*"} ${name ?: "*"}: $reason"
}
