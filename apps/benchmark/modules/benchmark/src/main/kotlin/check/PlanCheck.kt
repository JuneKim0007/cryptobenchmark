package io.github.junekim0007.cryptobench.benchmark.check

import io.github.junekim0007.cryptobench.benchmark.RefusedPlanException
import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.report.Skip
import io.github.junekim0007.cryptobench.settings.Metric
import java.security.Security

class PlanCheck(
    private val measurable: Set<Metric>,
    private val installedProviders: () -> Set<String> = { Security.getProviders().mapTo(LinkedHashSet()) { it.name } },
    private val energyCapability: () -> EnergyCapability? = { null },
) {

    class Checked(val runnable: List<BenchmarkCase>, val refused: List<Pair<BenchmarkCase, Refusal>>) {

        val skipped: List<Skip> get() = refused.map { (case, refusal) ->
            Skip(STAGE, case.provider, case.type, case.algorithm, refusal.toString())
        }
    }

    // Refused before any case is prepared: a refused case is left out with its reason; a run-wide refusal, or no case left, refuses the plan.
    fun runnable(cases: List<BenchmarkCase>, processRepetitions: Int): Checked {
        val refusals = check(cases, processRepetitions)
        val refused = refusals.mapTo(HashSet()) { it.caseId }
        val runnable = cases.filterNot { it.id in refused }
        if ("" in refused || runnable.isEmpty()) {
            throw RefusedPlanException(refusals)
        }
        return Checked(runnable, refusals.map { refusal -> cases.first { it.id == refusal.caseId } to refusal })
    }

    fun check(cases: List<BenchmarkCase>, processRepetitions: Int): List<Refusal> {
        val refusals = mutableListOf<Refusal>()
        if (cases.isEmpty()) {
            refusals += Refusal("", "nothing_to_measure")
        }
        if (processRepetitions < 1) {
            refusals += Refusal("", "not_positive: processRepetitions $processRepetitions")
        }
        val installed = installedProviders()
        val energy = energyRefusal(cases)
        cases.groupBy { it.id }
            .filterValues { it.size > 1 }
            .forEach { (id, duplicates) -> refusals += Refusal(id, "duplicate_case: ${duplicates.size} cases share this id") }
        cases.forEach { case -> refusals += refusalsFor(case, installed) }
        if (energy != null) {
            cases.filter { readsRails(it) }.forEach { refusals += Refusal(it.id, energy) }
        }
        return refusals
    }

    private fun energyRefusal(cases: List<BenchmarkCase>): String? {
        if (cases.none { readsRails(it) }) return null
        val capability = energyCapability()
            ?: return "energy_capability_unknown: push ${FileNames.ENERGY_CAPABILITY} from the pre-flight"
        return capability.refusal()
    }

    private fun capturesEnergy(case: BenchmarkCase): Boolean = Energy.of(case.harness.energy).capture != Energy.Capture.NONE

    private fun readsRails(case: BenchmarkCase): Boolean =
        capturesEnergy(case) && case.harness.energy.needsRails

    private fun refusalsFor(case: BenchmarkCase, installed: Set<String>): List<Refusal> {
        val refusals = mutableListOf<Refusal>()
        if (case.provider !in installed) {
            refusals += Refusal(case.id, "provider_not_installed: ${case.provider}, installed $installed")
        }
        if (case.operation == Operation.TYPE_DEFAULT) {
            refusals += Refusal(case.id, "not_measurable: ${case.type} has no operation this harness can time")
        }
        val unmeasurable = case.metrics - measurable
        if (unmeasurable.isNotEmpty()) {
            refusals += Refusal(case.id, "not_supported: metrics ${unmeasurable.map { it.name }}, this harness measures ${measurable.map { it.name }}")
        }
        return refusals
    }

    private companion object {
        const val STAGE = "benchmark"
    }
}
