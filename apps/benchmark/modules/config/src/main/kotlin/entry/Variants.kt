package io.github.junekim0007.cryptobench.config.entry

/** The execution paths a run or an entry asks for: the names, the default, the fallback of an invalid value, and which entries run them. */
object Variants {

    const val FIXED = "fixed"
    const val NOT_FIXED = "notFixed"
    const val SECURE = "secure"
    val NAMES = listOf(FIXED, NOT_FIXED, SECURE)
    val FALLBACK = listOf(FIXED)

    data class Read(val values: List<String>, val notice: String? = null)

    /** null when the key is absent; anything but a non-empty list of distinct names is [fixed] with a variants_fallback notice. */
    fun read(document: Map<String, Any>, key: String, path: String): Read? {
        if (key !in document) return null
        val value = document[key]
        val names = (value as? List<*>)?.takeIf { it.isNotEmpty() && it.all { name -> name is String && name in NAMES } && it.distinct().size == it.size }
        return names?.let { Read(it.map(Any?::toString)) }
            ?: Read(FALLBACK, "variants_fallback: $path $value is not a list of distinct $NAMES; $FALLBACK applies")
    }

    fun valid(values: List<String>): Boolean = values.all { it in NAMES } && values.distinct().size == values.size

    // the hardware-isolated key path is built for key generation only: an operation entry drops secure
    fun runnable(values: List<String>, generator: Boolean): List<String> = if (generator) values else values - SECURE

    fun secureNotice(askedBy: Int): String =
        "secure_path_unavailable: $askedBy entries ask for $SECURE; the hardware-isolated key path runs key generation only, so no $SECURE case runs for them"

    fun notFixedNotice(skipped: Int): String =
        "path_not_applicable: key generation takes $FIXED and $SECURE; $NOT_FIXED skipped for $skipped entries"
}
