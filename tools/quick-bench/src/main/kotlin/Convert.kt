import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.JetpackResults
import java.io.File

fun main(arguments: Array<String>) {
    if (arguments.size < 3) {
        System.err.println("usage: <benchmarkData.json> <prepared.yaml> <output directory>")
        return
    }
    val converted = JetpackResults.convert(File(arguments[0]).readText(), File(arguments[1]).readText())
    converted.missing.forEach { System.err.println("no_case_in_the_plan: $it") }
    val written = BenchmarkJson(File(arguments[2]).apply { mkdirs() }).write(converted.runtime, converted.rows)
    System.err.println("converted=${converted.rows.size} missing=${converted.missing.size}")
    println(written.path)
}
