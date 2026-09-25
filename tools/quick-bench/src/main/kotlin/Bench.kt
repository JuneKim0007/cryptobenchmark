import io.github.junekim0007.cryptobench.discovery.write.CaptureDocument
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import java.io.File

private var blackHole: Any? = null
private const val WARMUP_NANOS = 200_000_000L
private const val RUN_NANOS = 30_000_000L
private const val RUNS = 5

fun main(arguments: Array<String>) {
    val codec = YamlCodec()
    val capture = CaptureDocument.parse(codec.load(File(arguments[0]).readText()))
    val outputDirectory = File(arguments[3]).apply { mkdirs() }
    val run = Preparation(DiscoveryCapability(File(arguments[0]), File(arguments[1])), SkipFile(outputDirectory)).prepare(File(arguments[2]))
    System.err.println("prepared=${run.cases.size} skipped=${run.skipped.size}")

    val results = StringBuilder("{\n  \"runtime\": {\"javaVersion\": \"${capture.runtime.javaVersion}\", \"defaultKeySizeProperty\": \"${capture.runtime.defaultKeySizeProperty}\"},\n  \"cases\": [\n")
    run.cases.forEachIndexed { index, prepared ->
        val measurement = measure(prepared)
        results.append("    {\"id\": \"${prepared.case.id}\", \"type\": \"${prepared.case.type}\", \"algorithm\": \"${prepared.case.algorithm}\", \"provider\": \"${prepared.case.provider}\"")
        results.append(", \"operation\": \"${prepared.case.operation}\", \"keySize\": ${prepared.case.keySize}, \"inputSize\": ${prepared.case.inputSize}")
        results.append(", \"iterations\": ${measurement.iterations}, \"nanosPerOperation\": [${measurement.perOperation.joinToString(", ")}]}")
        results.append(if (index == run.cases.lastIndex) "\n" else ",\n")
        System.err.println("  ${prepared.case.id}: median ${measurement.perOperation.sorted()[RUNS / 2]} ns/op")
    }
    results.append("  ]\n}\n")
    File(outputDirectory, "benchmark.json").writeText(results.toString())
    System.err.println("blackHole=${blackHole?.javaClass?.simpleName}")
    println(File(outputDirectory, "benchmark.json").path)
}

private class Measurement(val iterations: Int, val perOperation: List<Long>)

private fun measure(prepared: PreparedCase): Measurement {
    val invocation = Invocations.of(prepared)
    var warmupIterations = 0L
    val warmupStart = System.nanoTime()
    while (System.nanoTime() - warmupStart < WARMUP_NANOS) {
        invocation.setUp()
        blackHole = invocation.perIteration()
        warmupIterations++
    }
    val perIteration = (System.nanoTime() - warmupStart).toDouble() / warmupIterations
    val iterations = maxOf(1, (RUN_NANOS / maxOf(1.0, perIteration)).toInt())
    val perOperation = (1..RUNS).map {
        val start = System.nanoTime()
        repeat(iterations) {
            invocation.setUp()
            blackHole = invocation.perIteration()
        }
        (System.nanoTime() - start) / iterations
    }
    return Measurement(iterations, perOperation)
}
