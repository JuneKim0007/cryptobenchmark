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
        document.append(runtime.entries.joinToString(", ") { (key, value) -> "${quoted(key)}: ${quoted(value)}" })
        document.append("},\n  \"cases\": [\n")
        rows.forEachIndexed { index, row ->
            document.append("    {\"id\": ${quoted(row.id)}, \"type\": ${quoted(row.type)}, \"algorithm\": ${quoted(row.algorithm)}, \"provider\": ${quoted(row.provider)}")
            document.append(", \"operation\": ${quoted(row.operation)}, \"keySize\": ${row.keySize}, \"inputSize\": ${row.inputSize}, \"keyKind\": ${quoted(row.keyKind)}")
            document.append(", \"${CaseDocument.VARIANT}\": ${quoted(row.variant)}")
            document.append(", \"$PARAMETERS\": ").append(parameters(row.parameters))
            row.thermalThrottleSleepSeconds?.let { document.append(", \"${CaseDocument.SLEEP}\": $it") }
            row.thermal?.let { document.append(", \"${CaseDocument.THERMAL}\": ").append(json(it)) }
            row.thermalNote?.let { document.append(", \"${CaseDocument.THERMAL_NOTE}\": ").append(escaped(it)) }
            row.gate?.let { document.append(", \"${CaseDocument.GATE}\": ").append(json(it)) }
            document.append(",\n     \"metrics\": {")
            document.append(row.metrics.entries.joinToString(", ") { (metric, samples) -> metricBlock(metric, samples) })
            document.append("}}")
            document.append(if (index == rows.lastIndex) "\n" else ",\n")
        }
        document.append("  ]\n}\n")
        return document.toString()
    }

    private fun metricBlock(metric: String, samples: MetricSamples): String =
        "${quoted(metric)}: {\"iterations\": ${samples.iterations}, \"runs\": [${samples.runs.joinToString(", ")}]${reported(samples.reported)}${origin(samples)}}"

    private fun origin(samples: MetricSamples): String =
        if (samples.kind == null) "" else ", \"source\": ${quoted(samples.source)}, \"kind\": ${quoted(samples.kind)}"

    private fun reported(stats: ReportedStats?): String =
        if (stats == null) "" else ", \"reported\": {\"minimum\": ${stats.minimum}, \"maximum\": ${stats.maximum}, \"median\": ${stats.median}, \"coefficientOfVariation\": ${stats.coefficientOfVariation}}"

    private fun quoted(value: String?): String = if (value == null) "null" else escaped(value)

    private fun parameters(fields: Map<String, Any>): String =
        fields.entries.joinToString(", ", "{", "}") { (key, value) -> "${escaped(key)}: ${if (value is Number) value else escaped(value.toString())}" }

    private fun json(value: Any?): String = when (value) {
        null -> "null"
        is Number -> if (value.toDouble().isFinite()) value.toString() else "null"
        is Boolean -> value.toString()
        is Map<*, *> -> value.entries.joinToString(", ", "{", "}") { (key, inner) -> "${escaped(key.toString())}: ${json(inner)}" }
        is List<*> -> value.joinToString(", ", "[", "]") { json(it) }
        else -> escaped(value.toString())
    }

    // RFC 8259: quote, backslash and every control character escaped; nothing else needs it.
    private fun escaped(text: String): String = buildString(text.length + 2) {
        append('"')
        for (char in text) {
            when {
                char == '"' -> append("\\\"")
                char == '\\' -> append("\\\\")
                char == '\n' -> append("\\n")
                char == '\t' -> append("\\t")
                char == '\r' -> append("\\r")
                char < ' ' -> append("\\u%04x".format(char.code))
                else -> append(char)
            }
        }
        append('"')
    }

    companion object {
        const val NAME = "benchmark.json"
        const val PARAMETERS = "parameters"
    }
}
