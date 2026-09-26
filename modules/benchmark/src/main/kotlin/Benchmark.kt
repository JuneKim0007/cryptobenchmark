package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.check.Refusal
import io.github.junekim0007.cryptobench.benchmark.run.CaseMeasurement
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedRun

class Benchmark(
    private val check: PlanCheck = PlanCheck(),
    private val onRefusal: (List<Refusal>) -> Unit = { refusals -> throw RefusedPlanException(refusals) },
) {

    fun measure(run: PreparedRun, measureCase: (PreparedCase) -> CaseMeasurement): List<CaseMeasurement> {
        val refusals = check.check(run)
        if (refusals.isNotEmpty()) {
            onRefusal(refusals)
        }
        val refused = refusals.mapTo(HashSet()) { it.caseId }
        return run.cases.filterNot { it.case.id in refused }.map { prepared -> measureCase(prepared) }
    }
}
