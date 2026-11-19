import io.github.junekim0007.cryptobench.benchmark.check.LaunchOrder
import io.github.junekim0007.cryptobench.benchmark.check.RunnablePlan
import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.ResultRow
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.discovery.write.CaptureDocument
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.files.FileNames
import java.io.File
import java.lang.management.ManagementFactory

// Every case prepared in listing order, then measured in the order file's; benchmark.json is rewritten as each case finishes, so a later failure,
// or this JVM's death, loses no earlier row.
fun main(arguments: Array<String>) = command(arguments, "<capture> <trial> <${FileNames.EFFECTIVE}> <benchmark output directory> <preparation directory> <order file>", { it.size == 6 }) {
    val preparationDirectory = File(arguments[4])
    val plan = hostPlan(File(arguments[0]), File(arguments[1]), File(arguments[2]), preparationDirectory.apply { mkdirs() })
    val capture = CaptureDocument.parse(YamlCodec.CAPTURE.load(File(arguments[0]).readText()))
    val output = BenchmarkJson(File(arguments[3]).apply { mkdirs() })
    val orderText = File(arguments[5]).readText()
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
    val byId = runnable.associateBy { it.case.id }
    for (prepared in LaunchOrder.of(plan.listed, orderText).mapNotNull(byId::get)) {
        val measured = plan.guarded(prepared.case, RunnablePlan.BENCHMARK, RunnablePlan.MEASURE_FAILED) { harness.measure(prepared) } ?: continue
        System.err.println("  ${prepared.case.id}: median ${measured.medianNanos} ns/op")
        rows += measured.row()
        output.write(runtime, rows)
    }
    check(rows.isNotEmpty()) { "nothing_measured: every prepared case failed, see ${File(preparationDirectory, FileNames.SKIPPED)}" }
    println(output.file.path)
}
