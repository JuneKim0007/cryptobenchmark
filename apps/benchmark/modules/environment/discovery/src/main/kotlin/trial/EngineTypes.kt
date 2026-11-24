package io.github.junekim0007.cryptobench.discovery.trial

import io.github.junekim0007.cryptobench.discovery.trial.requirement.ProbeKey
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames

// JCA engine types, folded, as the trials compare a captured service's type.
internal object EngineTypes {

    val GENERATOR = AlgorithmNames.fold(ProbeKey.GENERATOR)
    val PAIR_GENERATOR = AlgorithmNames.fold(ProbeKey.PAIR_GENERATOR)
    val FACTORY = AlgorithmNames.fold(ProbeKey.FACTORY)
    val GENERATORS = setOf(GENERATOR, PAIR_GENERATOR)
    val KEY_MAKERS = GENERATORS + FACTORY
    val DIGEST = AlgorithmNames.fold("MessageDigest")
    val CIPHER = AlgorithmNames.fold("Cipher")
}
