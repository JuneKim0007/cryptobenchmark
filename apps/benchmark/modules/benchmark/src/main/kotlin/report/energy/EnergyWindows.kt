package io.github.junekim0007.cryptobench.benchmark.report.energy

import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import java.io.File
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.files.FileNames

object EnergyWindows : DocumentReader<EnergyWindows.Read> {

    private const val SCHEMA_VERSION = 4

    override val schemaVersion = SCHEMA_VERSION

    class Read(val samples: Map<String, MetricSamples>, val notJoined: Map<String, List<String>>)

    fun read(energyText: String): Read = YamlFiles(YamlCodec.RESULTS).readOnly(File(FileNames.ENERGY_JSON), this).read(energyText)

    override fun parse(document: Map<String, Any>): Read {
        val source = document["source"]?.toString() ?: throw IllegalArgumentException("missing_field: source")
        val kind = document["kind"]?.toString() ?: throw IllegalArgumentException("missing_field: kind")
        val baseline = document["idleBaseline"]?.toString()
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
            samples[id] = MetricSamples(listOf((case["joulesPerOperation"] as Number).toDouble()), operations, source = source, kind = kind, idleBaseline = baseline)
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
