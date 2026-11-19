import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.PassMerge
import io.github.junekim0007.cryptobench.files.FileNames
import java.io.File

fun main(arguments: Array<String>) = command(arguments, "<output directory> <base ${FileNames.BENCHMARK_JSON}> [<metric key>=<${FileNames.BENCHMARK_JSON}> ...]",
    { it.size >= 2 && it.drop(2).all { pass -> '=' in pass } }) {
    val owned = arguments.drop(2).map { it.substringBefore('=') to File(it.substringAfter('=')).readText() }
    val merged = PassMerge.merge(File(arguments[1]).readText(), owned)
    merged.dropped.forEach { System.err.println(it) }
    check(merged.rows.isNotEmpty()) { "nothing_merged: no case of ${arguments[1]} survived the pass merge" }
    val written = BenchmarkJson(File(arguments[0]).apply { mkdirs() }).write(merged.runtime, merged.rows)
    System.err.println("merged=${merged.rows.size} passes=${owned.size + 1} metrics=${merged.rows.first().metrics.keys.joinToString(",")}")
    println(written.path)
}
