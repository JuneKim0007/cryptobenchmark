import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.discovery.write.CaptureDocument
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.record.PreparedFile
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import java.io.File

fun main(arguments: Array<String>) {
    HostBundled.fromEffective(File(arguments[2]))
    val capture = CaptureDocument.parse(YamlCodec().load(File(arguments[0]).readText()))
    val outputDirectory = File(arguments[3]).apply { mkdirs() }
    val preparationDirectory = File(arguments[4]).apply { mkdirs() }
    val run = Preparation(
        DiscoveryCapability(File(arguments[0]), File(arguments[1])),
        SkipFile(preparationDirectory),
        PreparedFile(preparationDirectory),
    ).prepare(File(arguments[2]))
    val checked = PlanCheck(HostHarness.METRICS).runnable(run)
    if (checked.refused.isNotEmpty()) {
        SkipFile(preparationDirectory).write(run.skipped + checked.skipped)
    }
    System.err.println("prepared=${run.cases.size} skipped=${run.skipped.size} refused=${checked.refused.size}")

    val harness = HostHarness()
    val measurements = checked.runnable.map { prepared ->
        harness.measure(prepared).also { System.err.println("  ${prepared.case.id}: median ${it.medianNanos} ns/op") }
    }
    val written = BenchmarkJson(outputDirectory).write(
        mapOf(
            "javaVersion" to capture.runtime.javaVersion,
            "defaultKeySizeProperty" to capture.runtime.defaultKeySizeProperty,
            "javaVendor" to capture.runtime.javaVendor,
            "javaRuntimeVersion" to capture.runtime.javaRuntimeVersion,
            "osName" to capture.runtime.osName,
            "osArch" to capture.runtime.osArch,
        ),
        measurements.map { it.row() },
    )
    println(written.path)
}
