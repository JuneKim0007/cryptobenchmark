package io.github.junekim0007.cryptobench.document.catalogue

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec

/** algorithms/groups.yaml's exemplars per family: the ids chosen to show its range, in the file's order. */
class GroupExemplars(private val byFamily: Map<String, List<String>>) {

    fun of(family: String): List<String> = byFamily[family].orEmpty()

    companion object {

        const val FILE = "groups.yaml"

        fun bundled(): GroupExemplars = parse(FamilyCatalogue.resource(FILE))

        fun parse(text: String): GroupExemplars = GroupExemplars(DocumentFields.section(YamlCodec.DOCUMENT.load(text), "groups").mapValues { (family, value) ->
            DocumentFields.optionalStrings(DocumentFields.asSection(value, family), "exemplars")
        })
    }
}
