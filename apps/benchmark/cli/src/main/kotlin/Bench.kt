import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.check.RunnablePlan
import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.ResultRow
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.discovery.write.CaptureDocument
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import java.io.File
import java.lang.management.ManagementFactory

// Every case prepared, then measured in turn; benchmark.json is rewritten as each case finishes, so a later failure, or this JVM's death, loses no earlier row.
fun main(arguments: Array<String>) = command {
    HostBundled.fromEffective(File(arguments[2]))
    val capture = CaptureDocument.parse(YamlCodec().load(File(arguments[0]).readText()))
    val output = BenchmarkJson(File(arguments[3]).apply { mkdirs() })
    val preparationDirectory = File(arguments[4]).apply { mkdirs() }
    val plan = RunnablePlan(Preparation(DiscoveryCapability(File(arguments[0]), File(arguments[1]))), PlanCheck(HostHarness.METRICS), preparationDirectory)
    val runnable = plan.preparedAll(File(arguments[2]))
    System.err.println("prepared=${runnable.size} skipped=${plan.skipped.size}")

    val runtime = mapOf(
        "javaVersion" to capture.runtime.javaVersion,
        "defaultKeySizeProperty" to capture.runtime.defaultKeySizeProperty,
        "javaVendor" to capture.runtime.javaVendor,
        "javaRuntimeVersion" to capture.runtime.javaRuntimeVersion,
        "osName" to capture.runtime.osName,
        "osArch" to capture.runtime.osArch,
    )
    val harness = HostHarness(collectionCount = { ManagementFactory.getGarbageCollectorMXBeans().sumOf { maxOf(0L, it.collectionCount) } })
    val rows = mutableListOf<ResultRow>()
    for (prepared in runnable) {
        val measured = plan.guarded(prepared.case, RunnablePlan.BENCHMARK, RunnablePlan.MEASURE_FAILED) { harness.measure(prepared) } ?: continue
        System.err.println("  ${prepared.case.id}: median ${measured.medianNanos} ns/op")
        rows += measured.row()
        output.write(runtime, rows)
    }
    check(rows.isNotEmpty()) { "nothing_measured: every prepared case failed, see ${File(preparationDirectory, FileNames.SKIPPED)}" }
    println(output.file.path)
}
