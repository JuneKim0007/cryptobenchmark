package io.github.junekim0007.cryptobench.config.entry

import io.github.junekim0007.cryptobench.files.VariantLabels

/** The execution paths a run or an entry asks for: the names, the fallback of an invalid value, and the ones a type runs. */
object Variants {

    const val FIXED = VariantLabels.FIXED
    const val NOT_FIXED = VariantLabels.NOT_FIXED
    const val SECURE = VariantLabels.SECURE
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

    /** The asked paths the type's catalogue row applies. */
    fun runnable(asked: List<String>, type: String): List<String> = asked.filter { it in EnginePaths.catalog.applicable(type) }

    fun secureUnavailable(subject: String): String =
        "secure_path_unavailable: $SECURE asked by $subject; the hardware-isolated key path runs ${EnginePaths.catalog.taking(SECURE).joinToString()} only"
}
