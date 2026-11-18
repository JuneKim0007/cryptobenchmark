package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.ContractOracle
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CrossProviderOracle
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import org.junit.Assert.assertEquals
import org.junit.Test
import org.yaml.snakeyaml.Yaml

/** Every operation of every setup-catalog type has its row in the check's operation-keyed tables: CrossProviderOracle.CHECKS and ContractOracle.PROPERTIES. */
class CatalogueTablesTest {

    @Suppress("UNCHECKED_CAST")
    private fun yaml(resource: String) = Yaml().load<Map<String, Any>>(javaClass.getResource(resource)!!.readText())

    @Suppress("UNCHECKED_CAST")
    private val operations: List<Operation> = run {
        val types = (yaml("/setup-catalog.yaml")["engines"] as Map<String, Any>).keys
        val rows = yaml("/io/github/junekim0007/cryptobench/preparation/engine/engine-operations.yaml")["types"] as Map<String, List<String>>
        types.flatMap { rows.getValue(it) }.map(Operation::valueOf).distinct()
    }

    private fun keys(owner: Class<*>, field: String): Set<*> = (owner.getDeclaredField(field).apply { isAccessible = true }.get(null) as Map<*, *>).keys

    @Test
    fun everyCatalogueOperationHasAPeerCheckAndContractProperties() {
        assertEquals(emptyList<Operation>(), operations - keys(CrossProviderOracle::class.java, "CHECKS"))
        assertEquals(emptyList<Operation>(), operations - keys(ContractOracle::class.java, "PROPERTIES"))
    }
}
