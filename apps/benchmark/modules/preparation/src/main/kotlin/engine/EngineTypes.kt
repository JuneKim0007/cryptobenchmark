package io.github.junekim0007.cryptobench.preparation.engine

import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields
import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec

class EngineTypes private constructor(
    private val types: Map<String, List<Operation>>,
    private val fallback: List<Operation>,
) {

    fun operationsOf(type: String): List<Operation> = types[EngineTypeName.fold(type)] ?: fallback

    companion object {

        // perf-repair reads the same file to know which used items the harness cannot time
        const val RESOURCE = FileNames.ENGINE_OPERATIONS

        private val loaded: EngineTypes by lazy {
            val text = EngineTypes::class.java.getResourceAsStream(RESOURCE)?.use { it.readBytes().toString(Charsets.UTF_8) }
                ?: throw IllegalStateException("missing_resource: $RESOURCE beside ${EngineTypes::class.java.name}")
            val document = YamlCodec().load(text)
            val types = DocumentFields.section(document, "types").entries.associate { (type, _) ->
                EngineTypeName.fold(type) to DocumentFields.strings(DocumentFields.section(document, "types"), type).map(Operation::valueOf)
            }
            EngineTypes(types, DocumentFields.strings(document, "fallback").map(Operation::valueOf))
        }

        fun standard(): EngineTypes = loaded
    }
}
