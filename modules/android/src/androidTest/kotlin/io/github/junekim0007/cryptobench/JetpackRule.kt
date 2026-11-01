package io.github.junekim0007.cryptobench

import android.annotation.SuppressLint
import androidx.benchmark.ExperimentalBenchmarkConfigApi
import androidx.benchmark.MicrobenchmarkScope
import androidx.benchmark.TestDefinition
import androidx.benchmark.measureRepeatedImplWithTracing
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import org.junit.rules.TestRule
import org.junit.runner.Description
import org.junit.runners.model.Statement

// BenchmarkRule always adds androidx's allocation phase; only this restricted entry point can leave it out.
@OptIn(ExperimentalBenchmarkConfigApi::class)
class JetpackRule(private val settings: CaseSettings) : TestRule {

    private var definition: TestDefinition? = null

    override fun apply(base: Statement, description: Description): Statement = object : Statement() {
        override fun evaluate() {
            definition = TestDefinition(description.className, description.testClass.simpleName, description.methodName)
            base.evaluate()
        }
    }

    @SuppressLint("RestrictedApi")
    fun measureRepeated(block: () -> Unit) {
        val test = checkNotNull(definition) { "not_applied: JetpackRule is not a @Rule of this test" }
        JetpackConfig.counterMismatch(settings)?.let { error(it) }
        measureRepeatedImplWithTracing(test, JetpackConfig.of(settings), JetpackConfig.timingOnly(settings), ::MicrobenchmarkScope) { _, iterations ->
            repeat(iterations) { block() }
        }
    }
}
