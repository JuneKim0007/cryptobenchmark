package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.testset.dto.Rule

internal fun Rule.matches(located: Inventory.Located): Boolean =
    matches(located.provider, located.type, located.name)
