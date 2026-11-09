import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.Merge
import io.github.junekim0007.cryptobench.files.FileNames
import java.io.File
import kotlin.system.exitProcess

fun main(arguments: Array<String>) {
    if (arguments.size < 2) {
        System.err.println("usage: <output directory> <${FileNames.BENCHMARK_JSON}> [<${FileNames.BENCHMARK_JSON}> ...]")
        exitProcess(2)
    }
    val merged = Merge.merge(arguments.drop(1).map { File(it).readText() })
    merged.dropped.forEach { System.err.println(it) }
    if (merged.rows.isEmpty()) {
        System.err.println("error: nothing_merged: no case survived the merge of ${arguments.size - 1} processes")
        exitProcess(1)
    }
    val written = BenchmarkJson(File(arguments[0]).apply { mkdirs() }).write(merged.runtime, merged.rows)
    val first = merged.rows.firstOrNull()
    System.err.println(
        "merged=${merged.rows.size} processes=${merged.processes} samples=${first?.time?.runs?.size ?: 0}" +
            " metrics=${first?.metrics?.keys?.joinToString(",") ?: "-"}",
    )
    println(written.path)
}
