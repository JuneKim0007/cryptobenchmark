package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames

internal fun Rule.matches(names: AlgorithmNames, located: Inventory.Located): Boolean =
    matches(names, located.provider, located.type, located.name)
