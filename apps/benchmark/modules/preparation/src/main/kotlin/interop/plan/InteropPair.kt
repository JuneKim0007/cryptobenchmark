package io.github.junekim0007.cryptobench.preparation.interop.plan

data class Member(val type: String, val algorithm: String, val provider: String) {

    init {
        require(type.isNotBlank() && algorithm.isNotBlank() && provider.isNotBlank()) { "missing_field: member type, algorithm or provider" }
    }

    override fun toString(): String = "$type|$algorithm|$provider"
}

data class InteropPair(val id: Int, val group: String, val a: Member, val b: Member, val keySize: Int?, val inputSize: Int?) {

    init {
        require(a.type == b.type) { "mixed_types: pair $id joins ${a.type} and ${b.type}" }
        require(keySize == null || keySize > 0) { "not_positive: pair $id keySize $keySize" }
        require(inputSize == null || inputSize > 0) { "not_positive: pair $id inputSize $inputSize" }
    }
}
