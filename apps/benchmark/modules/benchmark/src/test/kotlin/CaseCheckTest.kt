package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.run.OneCall
import io.github.junekim0007.cryptobench.benchmark.verify.CaseCheck
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswerFile
import io.github.junekim0007.cryptobench.benchmark.verify.record.CaseRecord
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class CaseCheckTest {

    private val check = CaseCheck(CaseCheck.oracles(KnownAnswerFile.read(CheckFixture.knownAnswers), CheckFixture.alone, HostHarness.ONCE), HostHarness.ONCE)

    @Suppress("UNCHECKED_CAST")
    private fun section(record: CaseRecord, vararg path: String): Map<String, Any> =
        path.fold(record.toMap()) { at, key -> at[key] as Map<String, Any> }

    private fun verdict(record: CaseRecord, oracle: String) = section(record, "oracles", oracle)["verdict"]

    @Test
    fun aDigestPassesItsVectorAndContractAndRecordsADeterministicDigest() {
        val record = check.check(CheckFixture.digest())
        assertEquals(CaseRecord.PASS, record.outcome)
        assertEquals("pass", verdict(record, "knownAnswer"))
        assertEquals("pass", verdict(record, "contract"))
        assertEquals("not_checkable", verdict(record, "crossProvider"))
        assertNotNull(record.toMap()["outputDigest"])
    }

    @Test
    fun theObservedStepsAreWhatEachVariantPlans() {
        val fixed = check.check(CheckFixture.gcmEncrypt(Variant.FIXED))
        assertEquals(listOf("init", "operation"), section(fixed, "observed")["steps"])
        assertEquals(1, section(fixed, "observed")["initsPerCall"])
        assertEquals("pass", verdict(fixed, "plan"))
        val notFixed = check.check(CheckFixture.gcmEncrypt(Variant.NOT_FIXED))
        assertEquals(listOf("getInstance", "init", "operation"), section(notFixed, "observed")["steps"])
    }

    @Test
    fun gcmEncryptMatchesTheNistVectorAndDrawsANewIvEachCall() {
        val record = check.check(CheckFixture.gcmEncrypt(keySize = 256))
        assertEquals(CaseRecord.PASS, record.outcome)
        assertEquals("pass", verdict(record, "knownAnswer"))
        assertEquals("pass", verdict(record, "nonce"))
        assertEquals("pass", (section(record, "oracles", "contract")["properties"] as Map<*, *>)["tamper"])
        assertNull("a keyed case has no comparable digest", record.toMap()["outputDigest"])
    }

    @Test
    fun aHarnessThatCallsMoreThanOnceFailsThePlan() {
        val twice = CaseCheck(emptyList(), OneCall { invocation, hook -> repeat(2) { hook.consume(invocation.once()) } })
        val record = twice.check(CheckFixture.digest())
        assertEquals(CaseRecord.FAIL, record.outcome)
        assertEquals("fail", verdict(record, "plan"))
    }

    @Test
    fun aCallThatThrowsIsAnErrorWithItsReason() {
        val failing = CaseCheck(emptyList(), OneCall { _, _ -> throw IllegalStateException("refused") })
        val record = failing.check(CheckFixture.digest())
        assertEquals(CaseRecord.ERROR, record.outcome)
        assertEquals("call_failed: IllegalStateException: refused", record.toMap()["reason"])
    }
}
