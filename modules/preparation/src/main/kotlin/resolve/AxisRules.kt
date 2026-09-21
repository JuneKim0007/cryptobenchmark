package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.measurement.EngineTypeName
import io.github.junekim0007.cryptobench.preparation.measurement.Operation

class AxisRules private constructor(
    private val rules: Map<String, AxisRule>,
    private val fallback: AxisRule,
) {

    fun of(type: String): AxisRule = rules[fold(type)] ?: fallback

    fun with(type: String, rule: AxisRule): AxisRules = AxisRules(rules + (fold(type) to rule), fallback)

    companion object {

        fun standard(): AxisRules = AxisRules(
            rules = mapOf(
                "Cipher" to AxisRule(usesKeySize = true, usesInputSize = true, operations = listOf(Operation.ENCRYPT, Operation.DECRYPT)),
                "Signature" to AxisRule(usesKeySize = true, usesInputSize = true, operations = listOf(Operation.SIGN, Operation.VERIFY)),
                "Mac" to AxisRule(usesKeySize = true, usesInputSize = true, operations = listOf(Operation.COMPUTE_MAC)),
                "MessageDigest" to AxisRule(usesKeySize = false, usesInputSize = true, operations = listOf(Operation.DIGEST)),
                "KeyGenerator" to AxisRule(usesKeySize = true, usesInputSize = false, operations = listOf(Operation.GENERATE_KEY)),
                "KeyPairGenerator" to AxisRule(usesKeySize = true, usesInputSize = false, operations = listOf(Operation.GENERATE_KEY_PAIR)),
                "KeyAgreement" to AxisRule(usesKeySize = true, usesInputSize = false, operations = listOf(Operation.AGREE_KEY)),
            ).mapKeys { (type, _) -> fold(type) },
            fallback = AxisRule(usesKeySize = true, usesInputSize = true, operations = listOf(Operation.TYPE_DEFAULT)),
        )

        private fun fold(type: String): String = EngineTypeName.fold(type)
    }
}
