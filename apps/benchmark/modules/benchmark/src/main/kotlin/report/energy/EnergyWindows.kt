package io.github.junekim0007.cryptobench.benchmark.report.energy

import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.files.FileNames

object EnergyWindows {

    private const val SCHEMA_VERSION = 2

    class Read(val samples: Map<String, MetricSamples>, val notJoined: Map<String, List<String>>)

    fun read(energyText: String): Read {
        val document = CaseDocument.load(energyText)
        require(document["schemaVersion"] == SCHEMA_VERSION) { "unsupported: ${FileNames.ENERGY_JSON} schemaVersion ${document["schemaVersion"]}" }
        val source = document["source"]?.toString() ?: throw IllegalArgumentException("missing_field: ${FileNames.ENERGY_JSON} source")
        val kind = document["kind"]?.toString() ?: throw IllegalArgumentException("missing_field: ${FileNames.ENERGY_JSON} kind")
        val samples = LinkedHashMap<String, MetricSamples>()
        val notJoined = LinkedHashMap<String, List<String>>()
        for ((id, value) in CaseDocument.optionalSection(document["cases"]).orEmpty()) {
            val case = CaseDocument.section(value)
            if (case["capture"] != "measured") continue
            if (case["valid"] != true) {
                notJoined[id] = (case["invalid"] as? List<*>)?.map { it.toString() }?.ifEmpty { null } ?: listOf("unjudged")
                continue
            }
            val problem = problem(case)
            if (problem != null) {
                notJoined[id] = listOf(problem)
                continue
            }
            val operations = (case["operations"] as Number).toInt()
            samples[id] = MetricSamples(listOf((case["joulesPerOperation"] as Number).toDouble()), operations, source = source, kind = kind)
        }
        return Read(samples, notJoined)
    }

    private fun problem(case: Map<String, Any>): String? {
        val perOperation = (case["joulesPerOperation"] as? Number)?.toDouble() ?: return "missing_field: joulesPerOperation"
        if (!perOperation.isFinite()) return "not_finite: joulesPerOperation $perOperation"
        val operations = (case["operations"] as? Number)?.toLong() ?: return "missing_field: operations"
        return if (operations in 1..Int.MAX_VALUE) null else "out_of_range: operations $operations"
    }
}
