package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.verify.CaseCheck
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswerFile
import io.github.junekim0007.cryptobench.benchmark.verify.record.CaseRecord
import io.github.junekim0007.cryptobench.benchmark.verify.record.CheckFile
import io.github.junekim0007.cryptobench.records.Skip
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** Characterization: check.yaml's bytes for a small fixture on the host: a digest, a MAC with a peer, a GCM encryption and one skip. */
class CheckFileGoldenTest {

    @get:Rule
    val folder = TemporaryFolder()

    @Test
    fun theCheckFileOfASmallFixture() {
        val check = CaseCheck(CaseCheck.oracles(KnownAnswerFile.read(CheckFixture.knownAnswers), CheckFixture.withPeer, HostHarness.ONCE), HostHarness.ONCE)
        val records = PeerProvider.installed { listOf(CheckFixture.digest(), CheckFixture.mac(), CheckFixture.gcmEncrypt()).map(check::check) } +
            CaseRecord.fromSkips(listOf(Skip("plan", "P", "Cipher", "AESWrap", "dry_run_failed: x")))
        val text = CheckFile.write(folder.root.resolve("check.yaml"), records, linkedMapOf("harness" to "host")).readText()
        assertEquals(EXPECTED, text)
    }

    private companion object {
        val EXPECTED = """
            schemaVersion: 1
            generatedFrom: {harness: host}
            summary:
              cases: 4
              outcomes: {pass: 3, notRun: 1}
              oracles:
                plan: {pass: 3}
                nonce: {not_checkable: 2, pass: 1}
                knownAnswer: {pass: 2, not_checkable: 1}
                crossProvider: {pass: 2, not_checkable: 1}
                contract: {pass: 3}
            cases:
            - id: MessageDigest_SHA-256_DIGEST_SUN_i64_WARM_fixed
              outcome: pass
              case: {type: MessageDigest, algorithm: SHA-256, provider: SUN, operation: DIGEST,
                variant: fixed, inputSize: 64}
              plan:
                perCall: operation
                steps: [operation]
              observed:
                calls: 1
                steps: [operation]
                newInstance: false
                initsPerCall: 0
                key: {kind: none}
              oracles:
                plan: {verdict: pass}
                nonce: {verdict: not_checkable, reason: 'no_iv: the engine reports none'}
                knownAnswer: {verdict: pass, vector: sha256-abc, source: 'https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/SHA256.pdf'}
                crossProvider:
                  verdict: pass
                  peers: {CheckPeer: pass}
                contract:
                  verdict: pass
                  properties: {length: pass, repeat: pass}
              outputDigest: 5a2dff7a2e453968af1ac4b36329955148b63e842f32a4a96e734e94b679913f
            - id: Mac_HmacSHA256_COMPUTE-MAC_SunJCE_k256_i64_WARM_fixed
              outcome: pass
              case: {type: Mac, algorithm: HmacSHA256, provider: SunJCE, operation: COMPUTE_MAC,
                variant: fixed, keySize: 256, inputSize: 64}
              plan:
                perCall: operation
                steps: [operation]
              observed:
                calls: 1
                steps: [operation]
                newInstance: false
                initsPerCall: 0
                key: {kind: secret, provider: SunJCE, by: same, class: javax.crypto.spec.SecretKeySpec}
              oracles:
                plan: {verdict: pass}
                nonce: {verdict: not_checkable, reason: 'no_iv: the engine reports none'}
                knownAnswer: {verdict: not_checkable, reason: 'no_vector: Mac.HmacSHA256 COMPUTE_MAC'}
                crossProvider:
                  verdict: pass
                  peers: {CheckPeer: pass}
                contract:
                  verdict: pass
                  properties: {length: pass, repeat: pass}
            - id: Cipher_AES-GCM-NoPadding_ENCRYPT_SunJCE_k128_i64_WARM_fixed
              outcome: pass
              case: {type: Cipher, algorithm: AES/GCM/NoPadding, provider: SunJCE, operation: ENCRYPT,
                variant: fixed, keySize: 128, inputSize: 64}
              plan:
                perCall: initAndOperation
                steps: [init, operation]
              observed:
                calls: 1
                steps: [init, operation]
                newInstance: false
                initsPerCall: 1
                iv: {by: harness, bytes: 12, distinctFromPreviousCall: true}
                key: {kind: secret, provider: SunJCE, by: same, class: javax.crypto.spec.SecretKeySpec}
              oracles:
                plan: {verdict: pass}
                nonce: {verdict: pass, by: harness}
                knownAnswer: {verdict: pass, vector: aes128-gcm-cavp-encryptextiv-pt256-count0,
                  source: 'https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Algorithm-Validation-Program/documents/mac/gcmtestvectors.zip#gcmEncryptExtIV128.rsp'}
                crossProvider:
                  verdict: not_checkable
                  reason: 'CheckPeer: peer_unavailable: NoSuchAlgorithmException: No such algorithm:
                    AES/GCM/NoPadding'
                  peers: {CheckPeer: not_checkable}
                contract:
                  verdict: pass
                  properties: {length: pass, reverse: pass, tamper: pass}
            - {id: plan|P|Cipher|AESWrap|dry_run_failed, outcome: notRun, stage: plan, reason: 'dry_run_failed:
                x', provider: P, type: Cipher, algorithm: AESWrap}

        """.trimIndent()
    }
}
