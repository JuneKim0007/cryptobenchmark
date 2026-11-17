package io.github.junekim0007.cryptobench.files

/** The execution paths a case runs, the last part of its id, and the refusal of a path a type does not apply; python's CONTRACT_PARTS must agree. */
object VariantLabels {
    const val FIXED = "fixed"
    const val NOT_FIXED = "notFixed"
    const val SECURE = "secure"

    /** The one path_not_applicable text, config's and preparation's. */
    fun notApplicable(subject: String, applies: List<String>, dropped: List<String>): String =
        "path_not_applicable: $subject applies $applies, $dropped dropped"
}
