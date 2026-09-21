package io.github.junekim0007.cryptobench.config.testset.dto

/** Matches provider, engine type and name; a missing part matches anything. Case-insensitive; `*` in a name is a wildcard. */
data class Rule(
    val provider: String? = null,
    val type: String? = null,
    val name: String? = null,
) {

    init {
        require(provider != null || type != null || name != null) { "empty_rule: give provider, type or name" }
        require(listOfNotNull(provider, type, name).none { it.isBlank() }) { "blank_rule_part: $this" }
    }

    private val namePattern: Regex? = name?.let { pattern ->
        Regex(pattern.split('*').joinToString(".*") { Regex.escape(it) }, RegexOption.IGNORE_CASE)
    }

    fun matches(provider: String, type: String, name: String): Boolean =
        (this.provider == null || this.provider.equals(provider, ignoreCase = true)) &&
            (this.type == null || this.type.equals(type, ignoreCase = true)) &&
            (namePattern == null || namePattern.matches(name))

    /** Higher is narrower: provider outweighs everything, an exact name outweighs a pattern, a pattern outweighs a type. */
    val specificity: Int
        get() = (if (provider != null) 8 else 0) +
            (if (type != null) 1 else 0) +
            when {
                name == null -> 0
                name.contains('*') -> 2
                else -> 4
            }

    override fun toString(): String = listOfNotNull(provider?.let { "provider=$it" }, type?.let { "type=$it" }, name?.let { "name=$it" }).joinToString(" ", "{", "}")
}
