package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.interop.InteropRun
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyCandidate
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.security.Security

/** Characterization: interop.yaml's bytes for a small plan on the JDK's own providers. */
class InteropFileGoldenTest {

    @get:Rule
    val folder = TemporaryFolder()

    private val jvm = object : DeviceCapability {
        override fun providers(): List<String> = Security.getProviders().map { it.name }
        override fun check(provider: String, type: String, algorithm: String): Availability =
            if (Security.getProvider(provider)?.getService(type, algorithm) != null) Availability.Available else Availability.Unavailable("not_registered")
        override fun measuredKey(provider: String, type: String, algorithm: String): KeyCandidate? =
            KeyCandidate(if (type == "Signature") algorithm.substringAfter("with").replace("ECDSA", "EC") else algorithm.substringBefore('/'))
    }

    private fun member(type: String, algorithm: String, provider: String) = "{type: $type, algorithm: $algorithm, provider: $provider}"

    @Test
    fun theInteropFileOfASmallPlan() {
        val pairs = listOf(
            member("MessageDigest", "SHA-256", "SUN") to member("MessageDigest", "SHA-256", "SUN"),
            member("MessageDigest", "SHA-256", "SUN") to member("MessageDigest", "SHA-512", "SUN"),
            member("Mac", "HmacSHA256", "SunJCE") to member("Mac", "HmacSHA256", "SunJCE"),
            member("Cipher", "AES/GCM/NoPadding", "SunJCE") to member("Cipher", "AES/GCM/NoPadding", "SunJCE"),
            member("Signature", "SHA256withECDSA", "SunEC") to member("Signature", "SHA384withECDSA", "SunEC"),
            member("Cipher", "AES/GCM/NoPadding", "SunJCE") to member("Cipher", "AES/GCM/NoPadding", "Missing"),
            member("KeyPairGenerator", "EC", "SunEC") to member("KeyPairGenerator", "EC", "SunEC"),
        )
        val plan = folder.newFile("interop_plan.yaml").apply {
            writeText("schemaVersion: 1\npairs:\n" + pairs.mapIndexed { i, (a, b) -> "- {id: ${i + 1}, group: g, a: $a, b: $b}\n" }.joinToString(""))
        }
        val out = folder.root.resolve("out/interop.yaml")
        InteropRun.run(jvm, plan, folder.newFile("probe_x.yaml"), out)
        assertEquals(EXPECTED, out.readText())
    }

    private companion object {
        val EXPECTED = """
            schemaVersion: 1
            generatedFrom: {plan: interop_plan.yaml, capture: probe_x.yaml}
            pairs:
            - id: 1
              group: g
              a: {type: MessageDigest, algorithm: SHA-256, provider: SUN}
              b: {type: MessageDigest, algorithm: SHA-256, provider: SUN}
              result: pass
              mode: same_output
              directions: {aToB: pass, bToA: pass}
              reason: ''
            - id: 2
              group: g
              a: {type: MessageDigest, algorithm: SHA-256, provider: SUN}
              b: {type: MessageDigest, algorithm: SHA-512, provider: SUN}
              result: fail
              mode: same_output
              directions: {aToB: fail, bToA: fail}
              reason: 'aToB: peer_differs: the peer computes other bytes from the same key, parameters
                and input; bToA: peer_differs: the peer computes other bytes from the same key,
                parameters and input'
            - id: 3
              group: g
              a: {type: Mac, algorithm: HmacSHA256, provider: SunJCE}
              b: {type: Mac, algorithm: HmacSHA256, provider: SunJCE}
              result: pass
              mode: same_output
              directions: {aToB: pass, bToA: pass}
              reason: ''
            - id: 4
              group: g
              a: {type: Cipher, algorithm: AES/GCM/NoPadding, provider: SunJCE}
              b: {type: Cipher, algorithm: AES/GCM/NoPadding, provider: SunJCE}
              result: pass
              mode: produce_consume
              directions: {aToB: pass, bToA: pass}
              reason: ''
            - id: 5
              group: g
              a: {type: Signature, algorithm: SHA256withECDSA, provider: SunEC}
              b: {type: Signature, algorithm: SHA384withECDSA, provider: SunEC}
              result: fail
              mode: produce_consume
              directions: {aToB: fail, bToA: fail}
              reason: 'aToB: peer_rejects: the peer does not verify the case''s signature; bToA:
                peer_rejects: the peer does not verify the case''s signature'
            - id: 6
              group: g
              a: {type: Cipher, algorithm: AES/GCM/NoPadding, provider: SunJCE}
              b: {type: Cipher, algorithm: AES/GCM/NoPadding, provider: Missing}
              result: not_checkable
              mode: none
              directions: {aToB: not_checkable, bToA: not_checkable}
              reason: 'aToB: not_registered: Cipher|AES/GCM/NoPadding|Missing: not_registered;
                bToA: not_registered: Cipher|AES/GCM/NoPadding|Missing: not_registered'
            - id: 7
              group: g
              a: {type: KeyPairGenerator, algorithm: EC, provider: SunEC}
              b: {type: KeyPairGenerator, algorithm: EC, provider: SunEC}
              result: pass
              mode: produce_consume
              directions: {aToB: pass, bToA: pass}
              reason: 'aToB: use Signature|SHA256withECDSA SIGN; bToA: use Signature|SHA256withECDSA
                SIGN'

        """.trimIndent()
    }
}
