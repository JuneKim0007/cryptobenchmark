package io.github.junekim0007.cryptobench.discovery.trial.keystore

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec

/** The generator catalogues' keystore blocks: the builder authorizations, and the key sizes or curves the trial generates. */
internal class KeystoreCatalogue(private val blocks: Map<Pair<String, String>, Block>) {

    data class Block(val authorizations: Map<String, Any>, val keySizes: List<Int> = emptyList(), val curves: List<String> = emptyList())

    /** The block of the first name the catalogue holds for this type, case-folded. */
    fun of(type: String, names: List<String>): Block? = names.firstNotNullOfOrNull { blocks[ServiceKey.fold(type) to ServiceKey.fold(it)] }

    companion object {

        val FILES = listOf("keygen.none_catalogue.yaml", "keypairgen.none_catalogue.yaml")
        private const val KEYSTORE = "keystore"
        private const val TRIAL_KEY_SIZES = "trialKeySizes"
        private const val TRIAL_CURVES = "trialCurves"
        private val LEAVES = setOf("source", "url", TRIAL_KEY_SIZES, TRIAL_CURVES)

        val bundled: KeystoreCatalogue by lazy {
            parse(FILES.map { name ->
                KeystoreCatalogue::class.java.getResource(name)?.readText() ?: throw IllegalStateException("missing_resource: $name is not beside ${KeystoreCatalogue::class.java.name}")
            })
        }

        fun parse(texts: List<String>): KeystoreCatalogue = KeystoreCatalogue(texts.flatMap { text ->
            DocumentFields.section(YamlCodec.DOCUMENT.load(text), "algorithms").mapNotNull { (id, row) ->
                val block = DocumentFields.optionalSection(DocumentFields.asSection(row, id), KEYSTORE) ?: return@mapNotNull null
                val type = id.substringBefore('|')
                (ServiceKey.fold(type) to ServiceKey.fold(id.substringAfter('|'))) to Block(block.filterKeys { it !in LEAVES },
                    DocumentFields.optionalNumbers(block, TRIAL_KEY_SIZES), DocumentFields.optionalStrings(block, TRIAL_CURVES))
            }
        }.toMap())
    }
}
