import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.check.RunnablePlan
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.verify.CaseCheck
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswerFile
import io.github.junekim0007.cryptobench.benchmark.verify.record.CaseRecord
import io.github.junekim0007.cryptobench.benchmark.verify.record.CheckFile
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import java.io.File

// The end-to-end check on the host JVM: every prepared case once through HostHarness.ONCE, all in this one process; writes check.yaml.
fun main(arguments: Array<String>) {
    require(arguments.size == 5) { "usage: <capture> <trial> <effective.yaml> <known-answers.yaml> <output directory>" }
    val (capture, trial, effective, knownAnswers, out) = arguments.map(::File)
    HostBundled.fromEffective(effective)
    val capability = DiscoveryCapability(capture, trial)
    val preparation = File(out, "preparation").apply { mkdirs() }
    val plan = RunnablePlan(Preparation(capability), PlanCheck(HostHarness.METRICS), preparation)
    val runnable = plan.preparedAll(effective)
    val check = CaseCheck(CaseCheck.oracles(KnownAnswerFile.read(knownAnswers), capability, HostHarness.ONCE), HostHarness.ONCE)
    val started = System.nanoTime()
    val records = runnable.map(check::check) + CaseRecord.notRun(plan.skipped)
    val millis = (System.nanoTime() - started) / 1_000_000
    val written = CheckFile.write(File(out, CheckFile.NAME), records,
        mapOf("harness" to "host", "effective" to effective.name, "capture" to capture.name, "knownAnswers" to knownAnswers.name, "millis" to millis))
    System.err.println("checked=${runnable.size} notRun=${records.size - runnable.size} millis=$millis")
    println(written.path)
}
