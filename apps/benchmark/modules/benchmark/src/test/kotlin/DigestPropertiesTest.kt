package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.ContractOracle
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.operation.PerCall
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import org.junit.Assert.assertEquals
import org.junit.Test
import javax.crypto.spec.IvParameterSpec

/** The repeat replays the call with the nonce it drew: a Mac random by bug fails it whether its nonce is fixed or drawn per call. */
class DigestPropertiesTest {

    private val fixed = BoundParameters.cycling(listOf(IvParameterSpec(ByteArray(12))))

    private fun fresh() = ParameterBinder().bind(mapOf("class" to "javax.crypto.spec.IvParameterSpec", "arguments" to listOf("fresh(12)")), "parameters")

    private fun properties(algorithm: String, parameters: BoundParameters): Map<*, *> = FakeMacProvider.installed {
        val base = CheckFixture.mac().let { it.copy(case = it.case.copy(algorithm = algorithm, provider = FakeMacProvider.NAME), parameters = parameters) }
        val prepared = base.copy(perCall = Invocations.of(base).perCall)
        assertEquals(PerCall.INIT_AND_OPERATION, prepared.perCall)
        val invocation = Invocations.of(prepared)
        repeat(2) { invocation.once() }
        ContractOracle().judge(CheckedCall(prepared, invocation, invocation.once())).details["properties"] as Map<*, *>
    }

    @Test
    fun aRandomMacFailsTheRepeatWithFixedParameters() {
        assertEquals(mapOf("length" to "pass", "repeat" to "fail"), properties(FakeMacProvider.RANDOM, fixed))
    }

    @Test
    fun aRandomMacFailsTheRepeatWithANonceDrawnPerCall() {
        assertEquals(mapOf("length" to "pass", "repeat" to "fail"), properties(FakeMacProvider.RANDOM, fresh()))
    }

    @Test
    fun aMacKeyedByItsDrawnNonceRepeats() {
        assertEquals("pass", properties(FakeMacProvider.NONCE_KEYED, fresh())["repeat"])
        assertEquals("pass", properties(FakeMacProvider.NONCE_KEYED, fixed)["repeat"])
    }
}
