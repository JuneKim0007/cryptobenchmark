package io.github.junekim0007.cryptobench.benchmark.preparation.resolve

import java.util.Locale

/** Engine type → axis rule. Types not registered still resolve, under the fallback rule. */
class AxisRules private constructor(
    private val rules: Map<String, AxisRule>,
    private val fallback: AxisRule,
) {

    fun of(type: String): AxisRule = rules[fold(type)] ?: fallback

    fun with(type: String, rule: AxisRule): AxisRules = AxisRules(rules + (fold(type) to rule), fallback)

    companion object {

        private val KEYED_INPUT = AxisRule(usesKeySize = true, usesInputSize = true)
        private val UNKEYED_INPUT = AxisRule(usesKeySize = false, usesInputSize = true)
        private val KEY_ONLY = AxisRule(usesKeySize = true, usesInputSize = false)

        fun standard(): AxisRules = AxisRules(
            rules = mapOf(
                "Cipher" to KEYED_INPUT,
                "Mac" to KEYED_INPUT,
                "Signature" to KEYED_INPUT,
                "MessageDigest" to UNKEYED_INPUT,
                "KeyGenerator" to KEY_ONLY,
                "KeyPairGenerator" to KEY_ONLY,
                "KeyAgreement" to KEY_ONLY,
            ).mapKeys { (type, _) -> fold(type) },
            fallback = KEYED_INPUT,
        )

        private fun fold(type: String): String = type.uppercase(Locale.ROOT)
    }
}
