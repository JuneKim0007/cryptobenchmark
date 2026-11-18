package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.preparation.operation.TypeDefaultDefinition
import org.junit.Assert.assertEquals
import org.junit.Test

/** Every setup-catalog type has its row in preparation's type-keyed tables: engine-operations.yaml and OperationDefinitions. */
class CatalogueTablesTest {

    private val types = DocumentFields.section(YamlCodec.DOCUMENT.load(javaClass.getResource("/setup-catalog.yaml")!!.readText()), "engines").keys

    @Test
    fun everyCatalogueTypeHasOperationsAndEachOperationADefinition() {
        val fallback = listOf(Operation.TYPE_DEFAULT)
        assertEquals(emptyList<String>(), types.filter { EngineTypes.standard().operationsOf(it) == fallback })
        val undefined = types.flatMap { type -> EngineTypes.standard().operationsOf(type).filter { OperationDefinitions.of(it) == TypeDefaultDefinition }.map { "$type.$it" } }
        assertEquals(emptyList<String>(), undefined)
    }
}
