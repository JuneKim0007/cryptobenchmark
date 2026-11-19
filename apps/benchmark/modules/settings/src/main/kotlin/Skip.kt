package io.github.junekim0007.cryptobench.settings

/** A case or entry left out; reason is `code: detail`, caseId only when one case is meant. skipped.yaml and report.yaml list them. */
data class Skip(
    val stage: String,
    val provider: String? = null,
    val type: String? = null,
    val name: String? = null,
    val reason: String,
    val caseId: String? = null,
) {

    init {
        require(stage.isNotBlank()) { "missing_field: stage" }
        require(CODE.matches(code)) { "invalid: skip reason without a code: $reason" }
    }

    val code: String get() = reason.substringBefore(SEPARATOR)

    val detail: String get() = reason.substringAfter(SEPARATOR, "")

    override fun toString(): String =
        "[$stage] ${provider ?: "*"} ${type ?: "*"} ${name ?: "*"}: ${caseId?.let { "$it: " } ?: ""}$reason"

    /** The record as both files write it. */
    fun fields(): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        put(STAGE, stage)
        provider?.let { put(PROVIDER, it) }
        type?.let { put(TYPE, it) }
        name?.let { put(NAME, it) }
        caseId?.let { put(CASE_ID, it) }
        put(CODE_FIELD, code)
        if (detail.isNotEmpty()) put(REASON, detail)
    }

    companion object {
        const val CONFIG = "config"
        const val PREPARATION = "preparation"

        private const val STAGE = "stage"
        private const val PROVIDER = "provider"
        private const val TYPE = "type"
        private const val NAME = "name"
        private const val CASE_ID = "caseId"
        private const val CODE_FIELD = "code"
        private const val REASON = "reason"
        private const val SEPARATOR = ": "
        private val CODE = Regex("[a-z][a-z0-9_]*")

        fun read(record: Map<String, *>): Skip {
            fun text(key: String) = record[key]?.toString()
            val code = text(CODE_FIELD) ?: throw IllegalArgumentException("missing_field: skipped $CODE_FIELD")
            return Skip(text(STAGE) ?: throw IllegalArgumentException("missing_field: skipped $STAGE"), text(PROVIDER), text(TYPE), text(NAME),
                        text(REASON)?.let { "$code$SEPARATOR$it" } ?: code, text(CASE_ID))
        }
    }
}
