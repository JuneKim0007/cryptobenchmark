package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.settings.OnFailure
import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.document.DocumentFields.choice
import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalString
import java.util.Locale

object PolicyDocument {

    private const val ON_FAILURE = "onFailure"

    fun of(policy: Policy): Map<String, Any> = linkedMapOf(ON_FAILURE to policy.onFailure.name.lowercase(Locale.ROOT))

    fun parse(document: Map<String, Any>, path: String): Policy {
        expectKeys(document, listOf(ON_FAILURE), path)
        val value = optionalString(document, ON_FAILURE).ifEmpty { return Policy() }
        return Policy(choice("$path.$ON_FAILURE", value, OnFailure.values().toList()) { it.name.lowercase(Locale.ROOT) })
    }
}
