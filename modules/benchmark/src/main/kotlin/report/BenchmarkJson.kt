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
            document.append(", \"operation\": \"${row.operation}\", \"keySize\": ${row.keySize}, \"inputSize\": ${row.inputSize}")
            document.append(", \"iterations\": ${row.iterations}, \"nanosPerOperation\": [${row.nanosPerOperation.joinToString(", ")}]}")
            document.append(if (index == rows.lastIndex) "\n" else ",\n")
        }
        document.append("  ]\n}\n")
        return document.toString()
    }

    companion object {
        const val NAME = "benchmark.json"
    }
}
