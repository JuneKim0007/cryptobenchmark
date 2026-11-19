import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.util.concurrent.TimeUnit

/** Every host main in its own JVM given no arguments, missing files and unreadable YAML: usage is exit 2, any failure one error line and exit 1, never a stack trace. */
class MainExitsTest {

    @get:Rule
    val folder = TemporaryFolder()

    private fun run(main: String, vararg arguments: String): String {
        val java = File(System.getProperty("java.home"), "bin/java").path
        val process = ProcessBuilder(listOf(java, "-cp", System.getProperty("java.class.path"), main) + arguments)
            .directory(folder.root).start()
        process.outputStream.close()
        val stderr = process.errorStream.bufferedReader().readLines().filterNot { it.startsWith("WARNING:") }
        process.inputStream.readBytes()
        check(process.waitFor(120, TimeUnit.SECONDS)) { "$main did not end" }
        val first = stderr.firstOrNull().orEmpty().replace(folder.root.canonicalPath, "<tmp>").replace(folder.root.path, "<tmp>")
        val trace = if (stderr.any { it.trimStart().startsWith("at ") }) " +trace" else ""
        return "$main ${arguments.size} args | exit ${process.exitValue()} | $first$trace"
    }

    private fun missing(name: String) = folder.root.resolve("missing/$name").path

    private fun bad(name: String) = folder.root.resolve(name).apply { writeText("a: [unclosed\n") }.path

    @Test
    fun everyMainKeepsOneContract() {
        val out = folder.newFolder("out").path
        val table = listOf(
            run("BenchKt"),
            run("BenchKt", missing("probe.yaml"), missing("trial.yaml"), missing("effective.yaml"), out, out, missing("order.txt")),
            run("BenchKt", bad("probe.yaml"), bad("trial.yaml"), bad("effective.yaml"), out, out, bad("order.txt")),
            run("CheckKt"),
            run("CheckKt", missing("probe.yaml"), missing("trial.yaml"), missing("effective.yaml"), missing("known-answers.yaml"), out),
            run("CheckKt", bad("probe.yaml"), bad("trial.yaml"), bad("effective.yaml"), bad("known-answers.yaml"), out),
            run("CheckConfigKt"),
            run("CheckConfigKt", missing("global.yaml")),
            run("CheckConfigKt", bad("global.yaml")),
            run("CheckDiffKt"),
            run("CheckDiffKt", missing("a.yaml"), missing("b.yaml")),
            run("CheckDiffKt", bad("a.yaml"), bad("b.yaml")),
            run("ConfigureKt"),
            run("ConfigureKt", missing("probe.yaml"), missing("trial.yaml"), out),
            run("ConfigureKt", bad("probe.yaml"), bad("trial.yaml"), out),
            run("ConvertKt"),
            run("ConvertKt", missing("benchmarkData.json"), missing("prepared.yaml"), out),
            run("ConvertKt", bad("benchmarkData.json"), bad("prepared.yaml"), out),
            run("MergePassesKt"),
            run("MergePassesKt", out, missing("benchmark.json")),
            run("MergePassesKt", out, bad("benchmark.json")),
            run("MergeRunsKt"),
            run("MergeRunsKt", out, missing("benchmark.json")),
            run("MergeRunsKt", out, bad("benchmark.json")),
            run("ListCasesKt"),
            run("ListCasesKt", missing("probe.yaml"), missing("trial.yaml"), missing("effective.yaml"), out),
            run("ListCasesKt", bad("probe.yaml"), bad("trial.yaml"), bad("effective.yaml"), out),
            run("InteropKt"),
            run("InteropKt", missing("probe.yaml"), missing("trial.yaml"), missing("effective.yaml"), missing("interop_plan.yaml"), missing("interop.yaml")),
            run("InteropKt", bad("probe.yaml"), bad("trial.yaml"), bad("effective.yaml"), bad("interop_plan.yaml"), out),
            run("ProbeKt"),
            run("ProbeKt", folder.root.resolve("discovery").path, folder.root.resolve("configuration").path, missing("global.yaml")),
            run("ProbeKt", folder.root.resolve("discovery").path, folder.root.resolve("configuration").path, bad("global.yaml")),
            run("RuntimeFieldsKt", "extra"),
        ).joinToString("\n")
        assertEquals(EXPECTED, table)
    }

    private companion object {
        // main and argument count | exit code | stderr's first line, +trace if a stack trace followed
        val EXPECTED = """
            BenchKt 0 args | exit 2 | usage: <capture> <trial> <effective.yaml> <benchmark output directory> <preparation directory> <order file>
            BenchKt 6 args | exit 1 | error: <tmp>/missing/effective.yaml (No such file or directory)
            BenchKt 6 args | exit 1 | error: while parsing a flow sequence
            CheckKt 0 args | exit 2 | usage: <capture> <trial> <effective.yaml> <known-answers.yaml> <output directory>
            CheckKt 5 args | exit 1 | error: <tmp>/missing/effective.yaml (No such file or directory)
            CheckKt 5 args | exit 1 | error: while parsing a flow sequence
            CheckConfigKt 0 args | exit 2 | usage: checkconfig <global.yaml>...
            CheckConfigKt 1 args | exit 1 | error: missing_file: <tmp>/missing/global.yaml
            CheckConfigKt 1 args | exit 1 | error: unreadable_yaml: global.yaml: while parsing a flow sequence
            CheckDiffKt 0 args | exit 2 | usage: <baseline check.yaml> <current check.yaml>
            CheckDiffKt 2 args | exit 1 | error: missing_file: <tmp>/missing/a.yaml
            CheckDiffKt 2 args | exit 1 | error: unreadable_yaml: a.yaml: while parsing a flow sequence
            ConfigureKt 0 args | exit 2 | usage: configure <probe_*.yaml> <trial_*.yaml> <configuration output directory> [<global.yaml>] [--facts=<facts.yaml>]
            ConfigureKt 3 args | exit 1 | error: missing_file: <tmp>/missing/probe.yaml
            ConfigureKt 3 args | exit 1 | error: unreadable_yaml: probe.yaml: while parsing a flow sequence
            ConvertKt 0 args | exit 2 | usage: <benchmarkData.json> <prepared.yaml> <output directory> [energy.json] [--metrics=TIME,...] [--samples=n] [--thermal=thermal.json] [--uncleaned]
            ConvertKt 3 args | exit 1 | error: <tmp>/missing/benchmarkData.json (No such file or directory)
            ConvertKt 3 args | exit 1 | error: while parsing a flow sequence
            MergePassesKt 0 args | exit 2 | usage: <output directory> <base benchmark.json> [<metric key>=<benchmark.json> ...]
            MergePassesKt 2 args | exit 1 | error: <tmp>/missing/benchmark.json (No such file or directory)
            MergePassesKt 2 args | exit 1 | error: while parsing a flow sequence
            MergeRunsKt 0 args | exit 2 | usage: <output directory> <benchmark.json> [<benchmark.json> ...]
            MergeRunsKt 2 args | exit 1 | error: <tmp>/missing/benchmark.json (No such file or directory)
            MergeRunsKt 2 args | exit 1 | error: while parsing a flow sequence
            ListCasesKt 0 args | exit 2 | usage: <capture> <trial> <effective.yaml> <preparation directory>
            ListCasesKt 4 args | exit 1 | error: <tmp>/missing/effective.yaml (No such file or directory)
            ListCasesKt 4 args | exit 1 | error: while parsing a flow sequence
            InteropKt 0 args | exit 2 | usage: <capture> <trial> <effective.yaml> <interop_plan.yaml> <interop.yaml>
            InteropKt 5 args | exit 1 | error: <tmp>/missing/effective.yaml (No such file or directory)
            InteropKt 5 args | exit 1 | error: while parsing a flow sequence
            ProbeKt 0 args | exit 2 | usage: probe <discovery output directory> [<configuration output directory>] [<global.yaml>] [--reuse]
            ProbeKt 3 args | exit 1 | error: missing_file: <tmp>/missing/global.yaml
            ProbeKt 3 args | exit 1 | error: unreadable_yaml: global.yaml: while parsing a flow sequence
            RuntimeFieldsKt 1 args | exit 2 | usage: runtimefields (no arguments)
        """.trimIndent()
    }
}
