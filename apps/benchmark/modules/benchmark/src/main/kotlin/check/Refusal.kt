package io.github.junekim0007.cryptobench.benchmark.check

data class Refusal(val caseId: String, val reason: String) {

    override fun toString(): String = if (caseId.isEmpty()) reason else "$caseId: $reason"
}
