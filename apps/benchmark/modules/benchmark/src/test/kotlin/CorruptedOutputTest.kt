package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.run.OneCall
import io.github.junekim0007.cryptobench.benchmark.run.OutputHook
import io.github.junekim0007.cryptobench.benchmark.verify.CaseCheck
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswerFile
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.ContractOracle
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CrossProviderOracle
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.KnownAnswerOracle
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.Oracle
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Each output oracle fails a call whose output has one flipped byte. */
class CorruptedOutputTest {

    private fun flipped(output: Any?): Any? = (output as? ByteArray)?.copyOf()?.also { it[0] = (it[0].toInt() xor 1).toByte() } ?: output

    private val corrupting = OneCall { invocation, hook -> hook.consume(flipped(invocation.once())) }

    private fun corrupted(prepared: PreparedCase): CheckedCall {
        val invocation = Invocations.of(prepared)
        val hook = OutputHook()
        corrupting.call(invocation, hook)
        return CheckedCall(prepared, invocation, hook.outputs.single())
    }

    private fun assertFails(oracle: Oracle, prepared: PreparedCase) {
        val outcome = oracle.judge(corrupted(prepared)).outcome
        assertTrue("${oracle.name} on ${prepared.case.id}: $outcome", outcome is Outcome.Fail)
    }

    @Test
    fun knownAnswerFailsAWrongByte() {
        val oracle = KnownAnswerOracle(KnownAnswerFile.read(CheckFixture.knownAnswers), corrupting)
        assertFails(oracle, CheckFixture.digest())
        assertFails(oracle, CheckFixture.gcmEncrypt(keySize = 256))
    }

    @Test
    fun crossProviderFailsWhatThePeerRecomputesDifferently() = PeerProvider.installed {
        assertFails(CrossProviderOracle(CheckFixture.withPeer), CheckFixture.digest())
        assertFails(CrossProviderOracle(CheckFixture.withPeer), CheckFixture.mac())
    }

    @Test
    fun contractFailsAnOutputItsOwnPropertiesRefuse() {
        assertFails(ContractOracle(), CheckFixture.digest())
        assertFails(ContractOracle(), CheckFixture.gcmEncrypt())
    }

    @Test
    fun throughTheCaseCheckTheKnownAnswerTakesTheCasesCorruptedCallToo() = PeerProvider.installed {
        val record = CaseCheck(CaseCheck.oracles(KnownAnswerFile.read(CheckFixture.knownAnswers), CheckFixture.withPeer, corrupting), corrupting).check(CheckFixture.digest())
        @Suppress("UNCHECKED_CAST")
        val verdicts = (record.toMap()["oracles"] as Map<String, Map<String, Any>>).mapValues { it.value["verdict"] }
        assertEquals(mapOf("knownAnswer" to "fail", "crossProvider" to "fail", "contract" to "fail"), verdicts.filterKeys { it in setOf("knownAnswer", "crossProvider", "contract") })
    }

    @Test
    fun theHonestCallPassesTheSameOracles() = PeerProvider.installed {
        val prepared = CheckFixture.digest()
        val invocation = Invocations.of(prepared)
        val hook = OutputHook()
        HostHarness.ONCE.call(invocation, hook)
        val call = CheckedCall(prepared, invocation, hook.outputs.single())
        for (oracle in listOf(KnownAnswerOracle(KnownAnswerFile.read(CheckFixture.knownAnswers), HostHarness.ONCE), CrossProviderOracle(CheckFixture.withPeer), ContractOracle())) {
            assertTrue(oracle.name, oracle.judge(call).outcome == Outcome.Pass)
        }
    }
}
