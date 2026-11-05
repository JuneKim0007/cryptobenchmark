package io.github.junekim0007.cryptobench.discovery.contract

data class ServiceRequirement(
    val provider: String,
    val type: String,
    val algorithm: String,
    val status: String,
    val className: String = "",
    val classRun: String = "",
    val transformationOf: String = "",
    val reason: String = "",
    val detail: String = "",
    val conditions: List<String> = emptyList(),
    val key: Map<String, Any> = emptyMap(),
    val runWith: Map<String, Any> = emptyMap(),
    val keysTried: List<Map<String, Any>> = emptyList(),
    val facts: Map<String, Any> = emptyMap(),
    val aliases: List<Map<String, Any>> = emptyList(),
    val millis: Long = 0,
) {

    init {
        require(status in STATUSES) { "unknown_status: $status" }
        require((status == RUNNABLE) == reason.isEmpty()) { "a record carries a reason exactly when it did not run" }
    }

    companion object {

        const val RUNNABLE = "runnable"
        const val NOT_RUNNABLE = "not_runnable"
        const val NO_CALL = "no_call"
        private val STATUSES = setOf(RUNNABLE, NOT_RUNNABLE, NO_CALL)

        const val PROVIDER_NOT_INSTALLED = "provider_not_installed"
        const val INSTANTIATION_FAILED = "instantiation_failed"
        const val NO_CALL_FOR_TYPE = "no_call_for_type"
        const val NO_KEY = "no_key"
        const val KEY_REFUSED = "key_refused"
        const val KEYSTORE_BORN_KEY = "keystore_born_key"
        const val GENERATION_REFUSED = "generation_refused"
        const val PARAMETERS_UNKNOWN = "parameters_unknown"
        const val OPERATION_REFUSED = "operation_refused"
        const val PROBE_FAILED = "probe_failed"

        const val KEYSTORE_BORN_CONDITION = "keystore-born key"
    }
}
