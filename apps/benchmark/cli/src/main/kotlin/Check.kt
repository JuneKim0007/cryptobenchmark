import io.github.junekim0007.cryptobench.benchmark.check.RunnablePlan
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.verify.CaseCheck
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswerFile
import io.github.junekim0007.cryptobench.benchmark.verify.record.CaseRecord
import io.github.junekim0007.cryptobench.benchmark.verify.record.CheckFile
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.files.Folders
import java.io.File

// The end-to-end check on the host JVM: every prepared case once through HostHarness.ONCE, all in this one process; writes check.yaml.
fun main(arguments: Array<String>) = command(arguments, "<capture> <trial> <${FileNames.EFFECTIVE}> <${FileNames.KNOWN_ANSWERS}> <output directory>", { it.size == 5 }) {
    val (capture, trial, effective, knownAnswers, out) = arguments.map(::File)
    val preparation = File(out, Folders.PREPARATION)
    val host = HostPlan(capture, trial, effective, preparation)
    preparation.mkdirs()
    val plan = host.plan
    val runnable = plan.preparedAll(effective)
    val check = CaseCheck(CaseCheck.oracles(KnownAnswerFile.read(knownAnswers), host.capability, HostHarness.ONCE), HostHarness.ONCE)
    val started = System.nanoTime()
    val checked = mutableListOf<CaseRecord>()
    // In finally: a check that ran out of memory stops here and still leaves its records.
    try {
        runnable.forEach { prepared -> plan.guarded(prepared.case, RunnablePlan.CHECK, RunnablePlan.CHECK_FAILED) { check.check(prepared) }?.let(checked::add) }
    } finally {
        val records = checked + CaseRecord.fromSkips(plan.skipped)
        val millis = (System.nanoTime() - started) / 1_000_000
        val file = CheckFile.write(File(out, FileNames.CHECK_RESULT), records,
            mapOf("harness" to "host", "effective" to effective.name, "capture" to capture.name, "knownAnswers" to knownAnswers.name, "millis" to millis))
        System.err.println("checked=${checked.size} notRun=${records.size - checked.size} millis=$millis")
        println(file.path)
    }
}
