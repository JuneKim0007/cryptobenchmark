package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalString
import java.util.Locale

/** The `policy` section, shared by global.yaml (as written) and effective.yaml (as frozen for later stages). */
object PolicyDocument {

    private const val ON_FAILURE = "onFailure"

    fun of(policy: Policy): Map<String, Any> = linkedMapOf(ON_FAILURE to policy.onFailure.name.lowercase(Locale.ROOT))

    fun parse(document: Map<String, Any>, path: String): Policy {
        expectKeys(document, listOf(ON_FAILURE), path)
        val value = optionalString(document, ON_FAILURE).ifEmpty { return Policy() }
        val choice = Policy.OnFailure.values().firstOrNull { it.name.equals(value, ignoreCase = true) }
            ?: throw IllegalArgumentException("invalid: $path.$ON_FAILURE $value, one of ${Policy.OnFailure.values().map { it.name.lowercase(Locale.ROOT) }}")
        return Policy(choice)
    }
}
