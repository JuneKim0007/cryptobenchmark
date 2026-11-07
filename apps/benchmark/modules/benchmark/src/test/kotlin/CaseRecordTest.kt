package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.verify.record.CaseRecord
import io.github.junekim0007.cryptobench.preparation.report.Skip
import org.junit.Assert.assertEquals
import org.junit.Test

class CaseRecordTest {

    private val first = Skip("plan", "BC", "Cipher", "AESWrap", "dry_run_failed: NegativeArraySizeException: -1")
    private val second = Skip("plan", "BC", "Cipher", "AESWrap", "dry_run_failed: Curve not supported: org.bouncycastle.jce.spec.ECNamedCurveSpec@4f76d764")

    private fun reasonsById(skips: List<Skip>) = CaseRecord.notRun(skips).associate { it.id to it.toMap()["reason"] }

    @Test
    fun notRunIdsDoNotDependOnTheSkipOrder() {
        assertEquals(reasonsById(listOf(first, second)), reasonsById(listOf(second, first)))
    }

    @Test
    fun recordedReasonsCarryNoIdentityHash() {
        assertEquals(setOf("dry_run_failed: NegativeArraySizeException: -1", "dry_run_failed: Curve not supported: org.bouncycastle.jce.spec.ECNamedCurveSpec"),
            reasonsById(listOf(first, second)).values.toSet())
    }
}
