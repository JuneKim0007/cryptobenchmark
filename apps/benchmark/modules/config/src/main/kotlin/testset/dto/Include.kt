package io.github.junekim0007.cryptobench.config.testset.dto

/** One include: the rule it selects with and the paths its entries ask for, null to inherit. */
data class Include(val rule: Rule, val variants: List<String>? = null)
