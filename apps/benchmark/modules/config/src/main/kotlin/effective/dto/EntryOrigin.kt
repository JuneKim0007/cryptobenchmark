package io.github.junekim0007.cryptobench.config.effective.dto

import io.github.junekim0007.cryptobench.config.testset.dto.Rule

/** The test-set file and every include, by its index there, that selected an effective entry; none: the set has no include and selects every entry. */
data class EntryOrigin(val testSet: String, val includes: Map<Int, Rule> = emptyMap())
