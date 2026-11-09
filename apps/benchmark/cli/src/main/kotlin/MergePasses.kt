import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.PassMerge
import io.github.junekim0007.cryptobench.files.FileNames
import java.io.File
import kotlin.system.exitProcess

fun main(arguments: Array<String>) {
    if (arguments.size < 2 || arguments.drop(2).any { '=' !in it }) {
        System.err.println("usage: <output directory> <base ${FileNames.BENCHMARK_JSON}> [<metric key>=<${FileNames.BENCHMARK_JSON}> ...]")
        exitProcess(2)
    }
    val owned = arguments.drop(2).map { it.substringBefore('=') to File(it.substringAfter('=')).readText() }
    val merged = PassMerge.merge(File(arguments[1]).readText(), owned)
    merged.dropped.forEach { System.err.println(it) }
    if (merged.rows.isEmpty()) {
        System.err.println("error: nothing_merged: no case of ${arguments[1]} survived the pass merge")
        exitProcess(1)
    }
    val written = BenchmarkJson(File(arguments[0]).apply { mkdirs() }).write(merged.runtime, merged.rows)
    System.err.println("merged=${merged.rows.size} passes=${owned.size + 1} metrics=${merged.rows.first().metrics.keys.joinToString(",")}")
    println(written.path)
}
