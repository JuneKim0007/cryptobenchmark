import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.energy.EnergyWindows
import io.github.junekim0007.cryptobench.benchmark.report.jetpack.JetpackResults
import java.io.File
import kotlin.system.exitProcess

private const val METRICS = "--metrics="
private const val SAMPLES = "--samples="
private const val THERMAL = "--thermal="
private val FLAGS = listOf(METRICS, SAMPLES, THERMAL)

fun main(arguments: Array<String>) {
    val (flags, positional) = arguments.partition { it.startsWith("--") }
    if (positional.size < 3 || flags.any { flag -> FLAGS.none { flag.startsWith(it) } }) {
        System.err.println("usage: <benchmarkData.json> <prepared.yaml> <output directory> [energy.json] [--metrics=TIME,...] [--samples=n] [--thermal=thermal.json]")
        exitProcess(2)
    }
    val metrics = flags.lastOrNull { it.startsWith(METRICS) }?.removePrefix(METRICS)?.split(',')
    val samples = flags.lastOrNull { it.startsWith(SAMPLES) }?.removePrefix(SAMPLES)?.toInt()
    val thermal = flags.firstOrNull { it.startsWith(THERMAL) }?.removePrefix(THERMAL)?.let { JetpackResults.thermalOf(File(it).readText()) }.orEmpty()
    val converted = JetpackResults.convert(File(positional[0]).readText(), File(positional[1]).readText(), energy(positional.getOrNull(3)), metrics, samples, thermal)
    converted.dropped.forEach { System.err.println(it) }
    converted.notApplied.forEach { System.err.println(it) }
    if (converted.rows.isEmpty()) {
        System.err.println("error: nothing_converted: no benchmark in ${positional[0]} gave a row")
        exitProcess(1)
    }
    val written = BenchmarkJson(File(positional[2]).apply { mkdirs() }).write(converted.runtime, converted.rows)
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
