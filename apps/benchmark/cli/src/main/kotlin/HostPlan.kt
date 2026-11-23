import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.check.RunnablePlan
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.contract.Handoff
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import java.io.File

// The host's plan, the one BenchKt measures, CheckKt checks and ListCasesKt lists: the effective file's bundled providers installed, then the capture and trial read once.
internal class HostPlan(capture: File, trial: File, effective: File, preparationDirectory: File) {

    init {
        HostBundled.fromEffective(effective)
    }

    val handoff: Handoff = Handoff.read(capture, trial)

    val capability = DiscoveryCapability(handoff)

    val plan = RunnablePlan(Preparation(capability), PlanCheck(HostHarness.METRICS), preparationDirectory)
}
