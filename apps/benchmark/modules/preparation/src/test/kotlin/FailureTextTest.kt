package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.interop.check.CrossCheck
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.shared.FailureText
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.InvalidKeyException

/** What preparation writes from a provider's failure (skipped.yaml, interop reasons) goes through the probe's scrubber: no key, at most 200 characters. */
class FailureTextTest {

    @Test
    fun aKeyInAFailureIsRemovedAndTheIdentityHashDropped() {
        ENCODINGS.forEach {
            assertEquals(it, "dry_run_failed: InvalidKeyException: key=<removed> on Spec", FailureText.of(InvalidKeyException("key=$it on Spec@4f76d764"), "dry_run_failed: "))
        }
    }

    @Test
    fun anOrdinaryFailureIsLeftAsItIs() {
        val text = "NoSuchAlgorithmException: Cannot find any provider supporting RSA/ECB/OAEPWithSHA-256AndMGF1Padding, sizes 16, 24, 32"
        assertEquals(text, FailureText.of(java.security.NoSuchAlgorithmException(text.substringAfter(": "))))
    }

    @Test
    fun aPrefixedReasonStaysWithinTheCap() {
        assertTrue(FailureText.of(IllegalStateException("provider detail ".repeat(40)), "key_generation_failed: ").length <= 200)
    }

    @Test
    fun anInteropReasonIsScrubbed() {
        val outcome = CrossCheck.classify(InvalidKeyException("key=${ENCODINGS.first()}")) as Outcome.NotCheckable
        assertEquals("key_or_parameters_rejected: InvalidKeyException: key=<removed>", outcome.reason)
    }

    private companion object {
        val ENCODINGS = listOf(
            "/quQaw7NZg9PtZvKiodfkg==",
            "9LT5_F_ilSBb_ptd0zfytsQJjmF7Ou8wtcMytxTn7-o",
            "fe ab 90 6b 0e cd 66 0f 4f b5 9b ca 8a 87 5f 92",
            "[-2, -85, -112, 107, 14, -51, 102, 15, 79, -75, -101, -54, -118, -121, 95, -110]",
            "932210a5754022dd",
        )
    }
}
