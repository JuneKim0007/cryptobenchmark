package io.github.junekim0007.cryptobench

import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.benchmark.run.OneCall
import io.github.junekim0007.cryptobench.benchmark.verify.CaseCheck
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswerFile
import io.github.junekim0007.cryptobench.benchmark.verify.record.CaseRecord
import io.github.junekim0007.cryptobench.benchmark.verify.record.CheckFile
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.AfterClass
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized
import java.io.File

// Run this class alone with -e androidx.benchmark.dryRunMode.enable true: every planned case once through Jetpack, all in one process.
@RunWith(Parameterized::class)
class EndToEndCheck(caseId: String, private val prepared: PreparedCase) : JetpackCase(caseId, CaseSettings.of(prepared.case)) {

    @Test
    fun callsTheCaseOnceAndChecksItsOutput() {
        check(InstrumentationRegistry.getArguments().getString(DRY_RUN) == "true") { "not_dry_run: launch with -e $DRY_RUN true, or every call is a timed loop" }
        val call = OneCall { invocation, hook -> once(invocation, hook) }
        records += CaseCheck(CaseCheck.oracles(vectors, DevicePlan.capability, call), call).check(prepared)
    }

    companion object {
        // Paired with apps/benchmark-runner/stages/check.py DRY_RUN.
        private const val DRY_RUN = "androidx.benchmark.dryRunMode.enable"
        private val records = mutableListOf<CaseRecord>()
        private val started = System.nanoTime()
        private val vectors by lazy { KnownAnswerFile.read(File(DevicePlan.directory, KnownAnswerFile.NAME)) }

        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> = CaseFilter.of(DevicePlan.cases) { it.case.id }.map { prepared -> arrayOf(prepared.case.id, prepared) }

        @JvmStatic
        @AfterClass
        fun write() {
            CheckFile.write(File(DevicePlan.directory, CheckFile.NAME), records + CaseRecord.notRun(DevicePlan.skipped),
                mapOf("harness" to "device", "millis" to (System.nanoTime() - started) / 1_000_000))
        }
    }
}
