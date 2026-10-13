import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.energy.EnergyWindows
import io.github.junekim0007.cryptobench.benchmark.report.jetpack.JetpackResults
import java.io.File

fun main(arguments: Array<String>) {
    if (arguments.size < 3) {
        System.err.println("usage: <benchmarkData.json> <prepared.yaml> <output directory> [energy.json]")
        return
    }
    val energyText = arguments.getOrNull(3)?.let { File(it).readText() }
    val energy = energyText?.let { EnergyWindows.measured(it) } ?: emptyMap()
    energyText?.let { EnergyWindows.invalid(it) }?.forEach { (id, reasons) -> System.err.println("energy_not_joined: $id: ${reasons.joinToString()}") }
    val converted = JetpackResults.convert(File(arguments[0]).readText(), File(arguments[1]).readText(), energy)
    converted.missing.forEach { System.err.println("no_case_in_the_plan: $it") }
    converted.notApplied.forEach { System.err.println(it) }
    val written = BenchmarkJson(File(arguments[2]).apply { mkdirs() }).write(converted.runtime, converted.rows)
    System.err.println("converted=${converted.rows.size} missing=${converted.missing.size}")
    println(written.path)
}
