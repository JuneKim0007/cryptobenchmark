package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.run.OutputHook
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CrossProviderOracle
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import javax.crypto.SecretKey

class CrossProviderOracleTest {

    private val oracle = CrossProviderOracle(CheckFixture.withPeer)

    // judgedAs: the case the oracle sees, where a test swaps what the call ran with.
    private fun judged(prepared: PreparedCase, judgedAs: PreparedCase = prepared): Outcome = PeerProvider.installed {
        val invocation = Invocations.of(prepared)
        val hook = OutputHook()
        HostHarness.ONCE.call(invocation, hook)
        oracle.judge(CheckedCall(judgedAs, invocation, hook.outputs.single())).outcome
    }

    @Test
    fun thePeerRecomputesTheCallsOwnDigestAndMac() {
        assertEquals(Outcome.Pass, judged(CheckFixture.digest()))
        assertEquals(Outcome.Pass, judged(CheckFixture.mac()))
    }

    @Test
    fun aKeyThePeerCannotRebuildIsNotCheckableWithItsCode() {
        val prepared = CheckFixture.mac()
        val real = prepared.key.secretKeyOrNull!!
        val sealed = object : SecretKey {
            override fun getAlgorithm() = real.algorithm
            override fun getFormat() = null
            override fun getEncoded(): ByteArray? = null
        }
        val outcome = judged(prepared, prepared.copy(key = KeyMaterial.Secret(sealed)))
        assertTrue(outcome.toString(), outcome is Outcome.NotCheckable && outcome.reason.startsWith("${PeerProvider.NAME}: peer_key_rejected: "))
    }
}
