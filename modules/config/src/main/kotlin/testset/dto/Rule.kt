package io.github.junekim0007.cryptobench.config.testset.dto

data class Rule(
    val provider: String? = null,
    val type: String? = null,
    val name: String? = null,
    val group: String? = null,
) {

    init {
        require(provider != null || type != null || name != null) { "empty_rule: give provider, type or name" }
        require(listOfNotNull(provider, type, name, group).none { it.isBlank() }) { "blank_rule_part: $this" }
        require(group == null || name != null) { "group_without_name: a group names one primitive measured more than once" }
        require(group == null || !group.contains('@')) { "invalid_group: $group" }
    }

    private val namePattern: Regex? = name?.let { pattern ->
        Regex(pattern.split('*').joinToString(".*") { Regex.escape(it) }, RegexOption.IGNORE_CASE)
    }

    fun matches(provider: String, type: String, name: String): Boolean =
        (this.provider == null || this.provider.equals(provider, ignoreCase = true)) &&
            (this.type == null || this.type.equals(type, ignoreCase = true)) &&
            (namePattern == null || namePattern.matches(name))

    fun appliesTo(group: String?): Boolean = this.group == null || this.group == group

    val specificity: Int
        get() = (if (group != null) 16 else 0) +
            (if (provider != null) 8 else 0) +
            (if (type != null) 1 else 0) +
            when {
                name == null -> 0
                name.contains('*') -> 2
                else -> 4
            }

    override fun toString(): String =
        listOfNotNull(provider?.let { "provider=$it" }, type?.let { "type=$it" }, name?.let { "name=$it" }, group?.let { "group=$it" })
            .joinToString(" ", "{", "}")
}
