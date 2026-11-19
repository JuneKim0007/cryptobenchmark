import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.energy.EnergyWindows
import io.github.junekim0007.cryptobench.benchmark.report.jetpack.JetpackResults
import io.github.junekim0007.cryptobench.files.FileNames
import java.io.File

private const val METRICS = "--metrics="
private const val SAMPLES = "--samples="
private const val THERMAL = "--thermal="
private const val UNCLEANED = "--uncleaned"
private val FLAGS = listOf(METRICS, SAMPLES, THERMAL, UNCLEANED)

fun main(arguments: Array<String>) = command(arguments,
    "<benchmarkData.json> <${FileNames.PREPARED}> <output directory> [${FileNames.ENERGY_JSON}] [--metrics=TIME,...] [--samples=n] [--thermal=thermal.json] [--uncleaned]",
    { it.count { argument -> !argument.startsWith("--") } >= 3 && it.filter { argument -> argument.startsWith("--") }.all { flag -> FLAGS.any { flag.startsWith(it) } } }) {
    val (flags, positional) = arguments.partition { it.startsWith("--") }
    val metrics = flags.lastOrNull { it.startsWith(METRICS) }?.removePrefix(METRICS)?.split(',')
    val samples = flags.lastOrNull { it.startsWith(SAMPLES) }?.removePrefix(SAMPLES)?.toInt()
    val thermal = flags.firstOrNull { it.startsWith(THERMAL) }?.removePrefix(THERMAL)?.let { JetpackResults.thermalOf(File(it).readText()) }.orEmpty()
    val converted = JetpackResults.convert(File(positional[0]).readText(), File(positional[1]).readText(), energy(positional.getOrNull(3)), metrics, samples, thermal, cleaned = UNCLEANED !in flags)
    converted.dropped.forEach { System.err.println(it) }
    converted.notApplied.forEach { System.err.println(it) }
    check(converted.rows.isNotEmpty()) { "nothing_converted: no benchmark in ${positional[0]} gave a row" }
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
