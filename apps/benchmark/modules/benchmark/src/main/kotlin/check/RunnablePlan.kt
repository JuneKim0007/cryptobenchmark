package io.github.junekim0007.cryptobench.benchmark.check

import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.global.OnFailure
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.prepare.Listing
import io.github.junekim0007.cryptobench.preparation.prepare.PreparationException
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.prepare.StoppedOnFailureException
import io.github.junekim0007.cryptobench.preparation.record.PreparedFile
import io.github.junekim0007.cryptobench.preparation.report.Skip
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import io.github.junekim0007.cryptobench.preparation.shared.FailureText
import java.io.File

/**
 * The orchestrator's side of a run: the listed cases the plan check lets through, each prepared on its own, and the one writer of
 * skipped.yaml and prepared.yaml. A case that fails at any stage is logged and skipped here; nothing else on the benchmark path catches.
 */
class RunnablePlan(
    private val preparation: Preparation,
    private val planCheck: PlanCheck,
    directory: File,
    private val log: (Skip) -> Unit = { System.err.println("skipped: $it") },
) {

    private val skipFile = SkipFile(directory)
    private val preparedFile = PreparedFile(directory)
    private val added = mutableListOf<Skip>()
    private lateinit var listing: Listing

    val skipped: List<Skip> get() = listing.skipped + refused + added

    private var refused: List<Skip> = emptyList()

    // written: false in a process given its cases by name, which adds to the files the listing wrote instead of replacing them.
    fun list(effective: File, written: Boolean): List<BenchmarkCase> {
        listing = preparation.list(effective)
        val checked = planCheck.runnable(listing.cases, listing.global.processRepetitions)
        refused = checked.skipped
        if (written) {
            skipFile.write(skipped)
            preparedFile.listed(listing, checked.runnable)
        }
        return checked.runnable
    }

    fun prepared(case: BenchmarkCase): PreparedCase? =
        guarded(case, Skip.PREPARATION, PREPARATION_FAILED, onFailure = { preparedFile.failed(case.id) }) {
            preparation.prepareOne(case).also(preparedFile::prepared)
        }

    // Every listed case prepared in turn; the host's one process for all of them.
    fun preparedAll(effective: File): List<PreparedCase> {
        val prepared = list(effective, written = true).mapNotNull(::prepared)
        stopIfSkipped()
        require(prepared.isNotEmpty()) { "nothing_prepared: every case was skipped, see ${skipFile.file}" }
        return prepared
    }

    fun <T> guarded(case: BenchmarkCase, stage: String, code: String, onFailure: () -> Unit = {}, block: () -> T): T? =
        try {
            block()
        } catch (failure: Throwable) {
            val reason = (failure as? PreparationException)?.reason ?: FailureText.of(failure, "$code: ")
            onFailure()
            Skip(stage, case.provider, case.type, case.algorithm, "${case.id}: $reason").also { skip ->
                added += skip
                skipFile.added(skip)
                log(skip)
            }
            null
        }

    // onFailure: stop: a rejected selection or a case preparation could not build stops the run, with every skip so far.
    fun stopIfSkipped() {
        val stopping = listing.skipped + added.filter { it.stage == Skip.PREPARATION }
        if (stopping.isNotEmpty() && listing.global.onFailure == OnFailure.STOP) throw StoppedOnFailureException(stopping)
    }

    companion object {
        const val PREPARATION_FAILED = "preparation_failed"
        const val MEASURE_FAILED = "measure_failed"
        const val CHECK_FAILED = "check_failed"
        const val BENCHMARK = "benchmark"
        const val CHECK = "check"
    }
}
