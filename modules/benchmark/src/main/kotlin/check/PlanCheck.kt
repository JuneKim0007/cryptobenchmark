package io.github.junekim0007.cryptobench.benchmark.check

import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedRun
import java.security.Security

class PlanCheck(private val installedProviders: () -> Set<String> = { Security.getProviders().mapTo(LinkedHashSet()) { it.name } }) {

    fun check(run: PreparedRun): List<Refusal> {
        val refusals = mutableListOf<Refusal>()
        if (run.cases.isEmpty()) {
            refusals += Refusal("", "nothing_to_measure")
        }
        if (run.processRepetitions < 1) {
            refusals += Refusal("", "not_positive: processRepetitions ${run.processRepetitions}")
        }
        val installed = installedProviders()
        run.cases.groupBy { it.case.id }
            .filterValues { it.size > 1 }
            .forEach { (id, duplicates) -> refusals += Refusal(id, "duplicate_case: ${duplicates.size} cases share this id") }
        run.cases.forEach { prepared -> refusals += refusalsFor(prepared, installed) }
        return refusals
    }

    private fun refusalsFor(prepared: PreparedCase, installed: Set<String>): List<Refusal> {
        val case = prepared.case
        val refusals = mutableListOf<Refusal>()
        if (case.provider !in installed) {
            refusals += Refusal(case.id, "provider_not_installed: ${case.provider}, installed $installed")
        }
        if (case.operation == Operation.TYPE_DEFAULT) {
            refusals += Refusal(case.id, "not_measurable: ${case.type} has no operation this harness can time")
        }
        val iterations = case.harness.iterations
        if (iterations != null && iterations < 1) {
            refusals += Refusal(case.id, "not_positive: iterations $iterations")
        }
        val inputSize = case.inputSize
        if (inputSize != null && inputSize <= 0) {
            refusals += Refusal(case.id, "not_positive: inputSize $inputSize")
        }
        return refusals
    }
}
