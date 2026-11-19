import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.check.RunnablePlan
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import java.io.File

// The host's plan, the one BenchKt measures and ListCasesKt lists: the effective file's bundled providers installed before the plan check reads them.
internal fun hostPlan(capture: File, trial: File, effective: File, preparationDirectory: File): RunnablePlan {
    HostBundled.fromEffective(effective)
    return RunnablePlan(Preparation(DiscoveryCapability(capture, trial)), PlanCheck(HostHarness.METRICS), preparationDirectory)
}
