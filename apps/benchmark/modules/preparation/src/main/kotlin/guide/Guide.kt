package io.github.junekim0007.cryptobench.preparation.guide

import io.github.junekim0007.cryptobench.preparation.request.Selection
import io.github.junekim0007.cryptobench.preparation.resolve.Rejection
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

/** guide.yaml: what the implementation guide says for this run's items. Effective says what runs; this says how each is built. */
class Guide(private val items: Map<String, Map<String, Any>>) {

    fun joined(selections: List<Selection>): Pair<List<Selection>, List<Rejection>> {
        val ready = mutableListOf<Selection>()
        val refused = mutableListOf<Rejection>()
        for (selection in selections) {
            val item = items["${selection.provider}/${selection.type}/${selection.algorithm}"]
            if (item == null) {
                refused += Rejection(selection, selection.provider, "not_in_guide: add an entry to measure it")
                continue
            }
            val never = DocumentFields.optionalString(item, "refused")
            if (never.isNotEmpty()) {
                refused += Rejection(selection, selection.provider, never)
                continue
            }
            val problem = DocumentFields.optionalString(item, "problem")
            if (problem.isNotEmpty() && selection.parameters.isEmpty()) {
                refused += Rejection(selection, selection.provider, problem)
                continue
            }
            val guided = item
            val accepted = DocumentFields.optionalNumbers(guided, "keySizes")
            val unsupported = if (accepted.isEmpty()) emptyList() else selection.keySizes - accepted.toSet()
            if (unsupported.isNotEmpty()) refused += Rejection(selection, selection.provider, "key_size_not_in_guide: $unsupported, the guide lists $accepted")
            val keySizes = selection.keySizes - unsupported.toSet()
            if (selection.keySizes.isNotEmpty() && keySizes.isEmpty()) continue
            ready += selection.copy(keySizes = keySizes, parameters = selection.parameters.ifEmpty { DocumentFields.optionalSection(guided, "parameters") })
        }
        return ready to refused
    }

    companion object {

        const val NAME = "guide.yaml"
        private const val SCHEMA_NAME = "guide"
        private const val SUPPORTED_SCHEMA_VERSION = 1

        fun beside(effectiveFile: File): Guide = read(File(effectiveFile.absoluteFile.parentFile, NAME))

        fun read(file: File): Guide {
            val items = LinkedHashMap<String, Map<String, Any>>()
            val document = DocumentFile.read(file, SCHEMA_NAME, SUPPORTED_SCHEMA_VERSION)
            for ((provider, types) in DocumentFields.optionalSection(document, "items")) for ((type, names) in DocumentFields.asSection(types, provider)) {
                for ((name, item) in DocumentFields.asSection(names, "$provider.$type")) items["$provider/$type/$name"] = DocumentFields.asSection(item, "$provider.$type.$name")
            }
            return Guide(items)
        }
    }
}
