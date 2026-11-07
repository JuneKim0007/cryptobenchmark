package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.prepare.CasePreparer
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedRun
import io.github.junekim0007.cryptobench.preparation.prepare.StoppedOnFailureException
import io.github.junekim0007.cryptobench.preparation.report.Skip
import io.github.junekim0007.cryptobench.preparation.global.OnFailure
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import io.github.junekim0007.cryptobench.preparation.resolve.CaseResolver
import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import io.github.junekim0007.cryptobench.preparation.record.PreparedFile
import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.preparation.request.PrimitiveReader
import java.io.File

class Preparation(
    capability: DeviceCapability,
    private val report: SkipFile,
    private val record: PreparedFile,
) {

    // One binder for the run: the selection check, key specs and case parameters bind through it.
    private val binder = ParameterBinder()
    private val resolver = CaseResolver(capability, binder)
    private val planner = KeyPlanner(capability)
    private val generator = KeyMaterialGenerator(binder = binder)

    fun prepare(effectiveFile: File): PreparedRun {
        val inbound = InboundFile.read(effectiveFile)
        val global = GlobalReader.read(inbound)
        val request = BenchmarkRequest(PrimitiveReader.read(inbound), global)
        val resolution = resolver.resolve(request)
        val skipped = resolution.rejections.mapTo(mutableListOf()) { rejection ->
            Skip(Skip.PREPARATION, rejection.provider, rejection.selection.type, rejection.selection.algorithm, rejection.reason)
        }
        val preparer = CasePreparer(planner, generator, binder)
        val prepared = mutableListOf<PreparedCase>()
        for (case in resolution.cases) {
            when (val outcome = preparer.prepare(case)) {
                is CasePreparer.Outcome.Prepared -> prepared += outcome.case
                is CasePreparer.Outcome.Skipped -> skipped += outcome.skip
            }
        }
        report.write(skipped)
        if (skipped.isNotEmpty() && global.onFailure == OnFailure.STOP) {
            throw StoppedOnFailureException(skipped)
        }
        require(prepared.isNotEmpty()) { "nothing_prepared: every case was skipped, see ${report.file}" }
        val run = PreparedRun(prepared, skipped, global.processRepetitions)
        record.write(run, inbound.fileName, inbound.runId, global.harness, global.seed)
        return run
    }
}
