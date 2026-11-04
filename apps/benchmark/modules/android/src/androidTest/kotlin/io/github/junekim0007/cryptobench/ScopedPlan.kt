package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import java.io.File

/** The before/after run in one process: bundled providers installed once, the run-level harness, the generated scopes and the call sites. */
object ScopedPlan {

    private val effective: File get() = File(DevicePlan.directory, "effective.yaml")

    private val installed: Unit by lazy {
        check(effective.isFile) { "missing_file: ${effective.absolutePath}, push effective.yaml first" }
        Bundled.installFrom(effective)
    }

    // The run-level harness of the pushed effective.yaml, the settings every CryptoBenchmark case inherits.
    val settings: CaseSettings by lazy {
        installed
        val global = GlobalReader.read(InboundFile.read(effective))
        CaseSettings.of(global.harness, global.metrics)
    }

    val scopes: List<Scope> by lazy {
        installed
        ScopeCatalog.load()
    }

    // Each entry is its case id and what prepares its timed call; a call site prepares only when the host names it.
    fun variants(): List<Array<Any>> = scopes.flatMap { scope ->
        listOf(arrayOf<Any>("scope:${scope.id}:before", { scope.before }), arrayOf<Any>("scope:${scope.id}:after", { scope.after }))
    } + run { installed; CallSitePlan.variants() }
}
