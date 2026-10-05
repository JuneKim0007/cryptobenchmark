package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.Skip
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStringOrNull
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.string

/** One skipped primitive as a map, shared by every file that records one. */
internal object SkipDocument {

    private const val STAGE = "stage"
    private const val PROVIDER = "provider"
    private const val TYPE = "type"
    private const val NAME = "name"
    private const val REASON = "reason"

    fun of(skip: Skip): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        put(STAGE, skip.stage)
        skip.provider?.let { put(PROVIDER, it) }
        skip.type?.let { put(TYPE, it) }
        skip.name?.let { put(NAME, it) }
        put(REASON, skip.reason)
    }

    fun parse(document: Map<String, Any>): Skip =
        Skip(string(document, STAGE), optionalStringOrNull(document, PROVIDER), optionalStringOrNull(document, TYPE), optionalStringOrNull(document, NAME), string(document, REASON))
}
