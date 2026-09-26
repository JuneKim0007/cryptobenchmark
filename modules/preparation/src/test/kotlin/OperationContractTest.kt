package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Test
import java.security.spec.AlgorithmParameterSpec

/**
 * What each operation says it consumes, checked against the JDK class it is measured on. A spec the
 * class accepts and no definition passes is a setting silently dropped, which is how EC key pairs
 * were measured on the provider's default curve instead of the one the config asked for.
 *
 * Key sizes are not checked this way: an int argument tells nothing about its meaning, and
 * Cipher.init(int, Key) takes the opmode, not a key size.
 */
class OperationContractTest {

    private val engines = mapOf(
        Operation.ENCRYPT to "javax.crypto.Cipher",
        Operation.DECRYPT to "javax.crypto.Cipher",
        Operation.SIGN to "java.security.Signature",
        Operation.VERIFY to "java.security.Signature",
        Operation.COMPUTE_MAC to "javax.crypto.Mac",
        Operation.DIGEST to "java.security.MessageDigest",
        Operation.GENERATE_KEY to "javax.crypto.KeyGenerator",
        Operation.GENERATE_KEY_PAIR to "java.security.KeyPairGenerator",
        Operation.AGREE_KEY to "javax.crypto.KeyAgreement",
    )

    private fun acceptsSpec(className: String): Boolean =
        Class.forName(className).methods.any { method ->
            method.parameterTypes.any { AlgorithmParameterSpec::class.java.isAssignableFrom(it) }
        }

    @Test
    fun anOperationPassesASpecExactlyWhenItsEngineTakesOne() {
        engines.forEach { (operation, className) ->
            val definition = OperationDefinitions.of(operation)
            assertEquals(
                "$operation is measured on $className: it takes a spec = ${acceptsSpec(className)}, the definition passes one = ${definition.consumesKeySpec || definition.consumesParameters}",
                acceptsSpec(className),
                definition.consumesKeySpec || definition.consumesParameters,
            )
        }
    }

    /**
     * `consumesInput` is the only answer about input: the input a case carries is derived from it, so
     * an operation that consumes none carries none, and one that does carries the seeded message of
     * its input size. DECRYPT and VERIFY build their own input from a key; OperationInputTest covers
     * those two.
     */
    @Test
    fun theInputACaseCarriesFollowsWhatTheOperationConsumes() {
        (Operation.entries - Operation.DECRYPT - Operation.VERIFY).forEach { operation ->
            val case = BenchmarkCase("Cipher", "AES/GCM/NoPadding", "SunJCE", operation, inputSize = 64, seed = 7)
            val definition = OperationDefinitions.of(operation)
            val input = definition.input(case, KeyMaterial.None, null)
            if (definition.consumesInput) {
                assertArrayEquals(operation.name, InputBytes.of(7, 64), (input as OperationInput.Message).bytes)
            } else {
                assertSame(operation.name, OperationInput.None, input)
            }
        }
    }

    @Test
    fun everyOperationExceptTheUnknownOneIsMeasuredOnAnEngine() {
        assertEquals(Operation.entries.toSet() - Operation.TYPE_DEFAULT, engines.keys)
    }
}
