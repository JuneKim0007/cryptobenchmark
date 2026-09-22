package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import org.junit.Assert.assertEquals
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

    @Test
    fun everyOperationExceptTheUnknownOneIsMeasuredOnAnEngine() {
        assertEquals(Operation.entries.toSet() - Operation.TYPE_DEFAULT, engines.keys)
    }
}
