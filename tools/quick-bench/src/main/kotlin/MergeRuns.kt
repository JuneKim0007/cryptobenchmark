import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.Merge
import java.io.File

fun main(arguments: Array<String>) {
    if (arguments.size < 2) {
        System.err.println("usage: <output directory> <benchmark.json> [<benchmark.json> ...]")
        return
    }
    val merged = Merge.merge(arguments.drop(1).map { File(it).readText() })
    val written = BenchmarkJson(File(arguments[0]).apply { mkdirs() }).write(merged.runtime, merged.rows)
    val first = merged.rows.firstOrNull()
    System.err.println(
        "merged=${merged.rows.size} processes=${merged.processes} samples=${first?.time?.runs?.size ?: 0}" +
            " metrics=${first?.metrics?.keys?.joinToString(",") ?: "-"}",
    )
    println(written.path)
}
