package io.github.junekim0007.cryptobench.preparation.interop.check

import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.operation.CaseArguments
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.security.InvalidAlgorithmParameterException
import java.security.InvalidKeyException
import java.security.SignatureException
import javax.crypto.BadPaddingException
import javax.crypto.IllegalBlockSizeException
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec

internal object CrossCheck {

    private val MESSAGE_BORNE = listOf(IvParameterSpec::class.java, GCMParameterSpec::class.java)

    fun produceConsume(producer: BenchmarkCase, consumer: BenchmarkCase, recipe: KeyRecipe, key: KeyMaterial): Outcome {
        val definition = OperationDefinitions.of(producer.operation)
        val artifact = try {
            travelling(definition.input(producer, key, null))
        } catch (failure: Exception) {
            return Outcome.Untestable("producer_failed: ${describe(failure)}")
        }
        return try {
            val returned = definition.invocation(PreparedCase(consumer, recipe, key, null, null, artifact)).once()
            if (returned is ByteArray && !returned.contentEquals(CaseArguments.seededMessage(producer))) {
                Outcome.Fail("consumer returned other bytes than the producer's message")
            } else Outcome.Pass
        } catch (failure: Exception) {
            classify(failure)
        }
    }

    fun sameOutput(first: BenchmarkCase, second: BenchmarkCase, recipe: KeyRecipe, key: KeyMaterial): Outcome {
        val outputs = try {
            listOf(first, second).map { case ->
                val definition = OperationDefinitions.of(case.operation)
                definition.invocation(PreparedCase(case, recipe, key, null, null, definition.input(case, key, null))).once()
            }
        } catch (failure: Exception) {
            return classify(failure)
        }
        val (a, b) = outputs
        return when {
            a !is ByteArray || b !is ByteArray -> Outcome.Untestable("outputs_not_comparable: ${a?.javaClass?.simpleName}")
            a.contentEquals(b) -> Outcome.Pass
            else -> Outcome.Fail("outputs differ for the same key and input")
        }
    }

    private fun travelling(artifact: OperationInput): OperationInput {
        if (artifact !is OperationInput.Ciphertext || artifact.providerParameters == null) return artifact
        val iv = MESSAGE_BORNE.any { spec -> runCatching { artifact.providerParameters.getParameterSpec(spec) }.isSuccess }
        return if (iv) artifact else OperationInput.Ciphertext(artifact.bytes, artifact.plaintextSize, artifact.spec, null)
    }

    fun classify(failure: Throwable): Outcome = when {
        failure is InvalidKeyException || failure is InvalidAlgorithmParameterException || failure is ClassCastException ->
            Outcome.Untestable("key_or_parameters_rejected: ${describe(failure)}")
        failure is BadPaddingException || failure is IllegalBlockSizeException || failure is SignatureException ||
            (failure is IllegalStateException && failure.message == "verify_failed") ->
            Outcome.Fail(describe(failure))
        else -> Outcome.Untestable("error: ${describe(failure)}")
    }

    private fun describe(failure: Throwable): String = "${failure.javaClass.simpleName}: ${failure.message}"
}
