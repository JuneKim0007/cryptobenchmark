package io.github.junekim0007.cryptobench.benchmark.report

import io.github.junekim0007.cryptobench.benchmark.run.CaseMeasurement
import java.io.File
import java.io.IOException

class BenchmarkJson(private val directory: File) {

    val file: File get() = File(directory, NAME)

    fun write(runtime: Map<String, String>, measurements: List<CaseMeasurement>): File {
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        file.writeText(text(runtime, measurements), Charsets.UTF_8)
        return file
    }

    fun text(runtime: Map<String, String>, measurements: List<CaseMeasurement>): String {
        val document = StringBuilder("{\n  \"runtime\": {")
        document.append(runtime.entries.joinToString(", ") { (key, value) -> "\"$key\": \"$value\"" })
        document.append("},\n  \"cases\": [\n")
        measurements.forEachIndexed { index, measurement ->
            val case = measurement.case
            document.append("    {\"id\": \"${case.id}\", \"type\": \"${case.type}\", \"algorithm\": \"${case.algorithm}\", \"provider\": \"${case.provider}\"")
            document.append(", \"operation\": \"${case.operation}\", \"keySize\": ${case.keySize}, \"inputSize\": ${case.inputSize}")
            document.append(", \"iterations\": ${measurement.iterations}, \"nanosPerOperation\": [${measurement.nanosPerOperation.joinToString(", ")}]}")
            document.append(if (index == measurements.lastIndex) "\n" else ",\n")
        }
        document.append("  ]\n}\n")
        return document.toString()
    }

    companion object {
        const val NAME = "benchmark.json"
    }
}
