package io.github.junekim0007.cryptobench.discovery.contract

data class AliasEntry(
    val type: String,
    val name: String,
    val target: String,
) {

    init {
        require(type.isNotBlank()) { "missing_field: type" }
        require(name.isNotBlank()) { "missing_field: name" }
        require(target.isNotBlank()) { "missing_field: target" }
    }

    override fun toString(): String = "$type.$name -> $target"
}
