import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.energy.EnergyWindows
import io.github.junekim0007.cryptobench.benchmark.report.jetpack.JetpackResults
import java.io.File
import kotlin.system.exitProcess

private const val METRICS_FLAG = "--metrics="

fun main(arguments: Array<String>) {
    val (flags, paths) = arguments.partition { it.startsWith(METRICS_FLAG) }
    if (paths.size < 3) {
        System.err.println("usage: <benchmarkData.json> <prepared.yaml> <output directory> [energy.json] [$METRICS_FLAG<TIME,ALLOCATION,...>]")
        exitProcess(2)
    }
    val metrics = flags.lastOrNull()?.removePrefix(METRICS_FLAG)?.split(",")
    val converted = JetpackResults.convert(File(paths[0]).readText(), File(paths[1]).readText(), energy(paths.getOrNull(3)), metrics)
    converted.dropped.forEach { System.err.println(it) }
    converted.notApplied.forEach { System.err.println(it) }
    if (converted.rows.isEmpty()) {
        System.err.println("error: nothing_converted: no benchmark in ${paths[0]} gave a row")
        exitProcess(1)
    }
    val written = BenchmarkJson(File(paths[2]).apply { mkdirs() }).write(converted.runtime, converted.rows)
    System.err.println("converted=${converted.rows.size} dropped=${converted.dropped.size}")
    println(written.path)
}

// Timing never depends on energy: an energy.json that cannot be read joins nothing.
private fun energy(path: String?): Map<String, MetricSamples> {
    val text = path?.let { File(it).readText() } ?: return emptyMap()
    val read = try {
        EnergyWindows.read(text)
    } catch (unreadable: RuntimeException) {
        System.err.println("energy_not_joined: $path: ${unreadable.message}")
        return emptyMap()
    }
    read.notJoined.forEach { (id, reasons) -> System.err.println("energy_not_joined: $id: ${reasons.joinToString()}") }
    return read.samples
}
