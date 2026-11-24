package io.github.junekim0007.cryptobench.discovery.trial.keystore

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames

/** The generator catalogues' keystore blocks: the builder authorizations, and the key sizes or curves the trial generates. */
internal class KeystoreCatalogue(private val blocks: Map<Pair<String, String>, Block>) {

    data class Block(val authorizations: Map<String, Any>, val keySizes: List<Int> = emptyList(), val curves: List<String> = emptyList())

    /** The block of the first name the catalogue holds for this type, case-folded. */
    fun of(type: String, names: List<String>): Block? = names.firstNotNullOfOrNull { blocks[AlgorithmNames.fold(type) to AlgorithmNames.fold(it)] }

    companion object {

        private const val KEYSTORE = "keystore"
        private const val TRIAL_KEY_SIZES = "trialKeySizes"
        private const val TRIAL_CURVES = "trialCurves"
        private val LEAVES = setOf("source", "url", TRIAL_KEY_SIZES, TRIAL_CURVES)

        val bundled: KeystoreCatalogue by lazy { of(FamilyCatalogue.bundled(FamilyCatalogue.GENERATORS)) }

        fun of(catalogue: FamilyCatalogue): KeystoreCatalogue = KeystoreCatalogue(catalogue.entries.mapNotNull { entry ->
            @Suppress("UNCHECKED_CAST")
            val block = entry.section(KEYSTORE) as Map<String, Any>? ?: return@mapNotNull null
            (AlgorithmNames.fold(entry.type) to AlgorithmNames.fold(entry.name)) to Block(block.filterKeys { it !in LEAVES },
                DocumentFields.optionalNumbers(block, TRIAL_KEY_SIZES), DocumentFields.optionalStrings(block, TRIAL_CURVES))
        }.toMap())
    }
}
