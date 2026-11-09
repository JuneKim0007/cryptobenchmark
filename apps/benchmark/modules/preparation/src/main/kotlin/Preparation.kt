package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.preparation.guide.Guide
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.prepare.CasePreparer
import io.github.junekim0007.cryptobench.preparation.prepare.Listing
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.report.Skip
import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.preparation.request.PrimitiveReader
import io.github.junekim0007.cryptobench.preparation.resolve.CaseResolver
import io.github.junekim0007.cryptobench.preparation.resolve.Resolution
import java.io.File

/** list: the cases of an effective file, no provider called; prepareOne: one named case built and called once, or a throw. Writes no file. */
class Preparation(capability: DeviceCapability) {

    // One binder for the run: the selection check, key specs and case parameters bind through it.
    private val binder = ParameterBinder()
    private val resolver = CaseResolver(capability, binder)
    private val preparer = CasePreparer(KeyPlanner(capability), KeyMaterialGenerator(binder = binder), binder)

    fun list(effectiveFile: File): Listing {
        val inbound = InboundFile.read(effectiveFile)
        val global = GlobalReader.read(inbound)
        val (ready, refused) = Guide.beside(effectiveFile).joined(PrimitiveReader.read(inbound))
        val resolution = if (ready.isEmpty()) Resolution(emptyList(), emptyList()) else resolver.resolve(BenchmarkRequest(ready, global))
        val skipped = (refused + resolution.rejections).map { rejection ->
            Skip(Skip.PREPARATION, rejection.provider, rejection.selection.type, rejection.selection.algorithm, rejection.reason)
        }
        return Listing(resolution.cases, skipped, global, inbound.fileName, inbound.runId)
    }

    fun prepareOne(case: BenchmarkCase): PreparedCase = preparer.prepare(case)
}
