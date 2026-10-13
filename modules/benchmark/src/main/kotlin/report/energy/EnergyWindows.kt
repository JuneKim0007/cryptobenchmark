package io.github.junekim0007.cryptobench.benchmark.report.energy

import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples

object EnergyWindows {

    fun invalid(energyText: String): Map<String, List<String>> {
        val cases = CaseDocument.optionalSection(CaseDocument.load(energyText)["cases"]) ?: return emptyMap()
        return cases.mapValues { (_, value) -> CaseDocument.section(value) }
            .filter { (_, case) -> case["capture"] == "measured" && case["valid"] != true }
            .mapValues { (_, case) -> (case["invalid"] as? List<*>)?.map { it.toString() } ?: listOf("unjudged") }
    }

    fun measured(energyText: String): Map<String, MetricSamples> {
        val document = CaseDocument.load(energyText)
        require(document["schemaVersion"] == 1) { "unsupported: energy.json schemaVersion ${document["schemaVersion"]}" }
        val cases = CaseDocument.optionalSection(document["cases"]) ?: return emptyMap()
        return cases.mapNotNull { (id, value) ->
            val case = CaseDocument.section(value)
            if (case["capture"] != "measured" || case["valid"] != true) return@mapNotNull null
            val perOperation = (case["joulesPerOperation"] as? Number)?.toDouble()
                ?: throw IllegalArgumentException("missing_field: energy.json $id.joulesPerOperation")
            val operations = (case["operations"] as? Number)?.toLong()
                ?: throw IllegalArgumentException("missing_field: energy.json $id.operations")
            require(operations in 1..Int.MAX_VALUE) { "out_of_range: energy.json $id.operations $operations" }
            id to MetricSamples(listOf(perOperation), operations.toInt())
        }.toMap()
    }
}
