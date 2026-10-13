package io.github.junekim0007.cryptobench.benchmark.report

import java.io.File
import java.io.IOException

class BenchmarkJson(private val directory: File) {

    val file: File get() = File(directory, NAME)

    fun write(runtime: Map<String, String>, rows: List<ResultRow>): File {
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        file.writeText(text(runtime, rows), Charsets.UTF_8)
        return file
    }

    fun text(runtime: Map<String, String>, rows: List<ResultRow>): String {
        val document = StringBuilder("{\n  \"runtime\": {")
        document.append(runtime.entries.joinToString(", ") { (key, value) -> "\"$key\": \"$value\"" })
        document.append("},\n  \"cases\": [\n")
        rows.forEachIndexed { index, row ->
            document.append("    {\"id\": \"${row.id}\", \"type\": \"${row.type}\", \"algorithm\": \"${row.algorithm}\", \"provider\": \"${row.provider}\"")
            document.append(", \"operation\": \"${row.operation}\", \"keySize\": ${row.keySize}, \"inputSize\": ${row.inputSize}, \"keyKind\": ${quoted(row.keyKind)}")
            document.append(legacyTime(row))
            document.append(",\n     \"metrics\": {")
            document.append(row.metrics.entries.joinToString(", ") { (metric, samples) -> metricBlock(metric, samples) })
            document.append("}}")
            document.append(if (index == rows.lastIndex) "\n" else ",\n")
        }
        document.append("  ]\n}\n")
        return document.toString()
    }

    private fun metricBlock(metric: String, samples: MetricSamples): String =
        "\"$metric\": {\"iterations\": ${samples.iterations}, \"runs\": [${samples.runs.joinToString(", ")}]${reported(samples.reported)}}"

    private fun reported(stats: ReportedStats?): String =
        if (stats == null) "" else ", \"reported\": {\"minimum\": ${stats.minimum}, \"maximum\": ${stats.maximum}, \"median\": ${stats.median}, \"coefficientOfVariation\": ${stats.coefficientOfVariation}}"

    private fun quoted(value: String?): String = if (value == null) "null" else "\"$value\""

    // Transitional duplicate of metrics.timeNs: tools/quick-bench/analyze.py still reads this flat pair.
    private fun legacyTime(row: ResultRow): String {
        val time = row.time ?: return ""
        return ",\n     \"iterations\": ${time.iterations}, \"nanosPerOperation\": [${time.runs.joinToString(", ")}]"
    }

    companion object {
        const val NAME = "benchmark.json"
    }
}
