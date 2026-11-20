import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import org.junit.Assert.assertEquals
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.security.Provider
import java.security.PublicKey
import java.security.Security
import java.security.interfaces.ECPublicKey
import java.security.interfaces.XECPublicKey
import java.security.spec.NamedParameterSpec
import javax.crypto.KeyAgreement
import javax.crypto.interfaces.DHPublicKey

/** An agreement case's two pairs as KeyMaterialGenerator makes them (count = 2, the second through PeerPair): they share parameters and agree.
 * BC runs only with -PbundledArtifacts=org.bouncycastle:bcprov-jdk18on:<version> on the cli build, as .github/workflows/jca-contract.yml does. */
class PeerPairsTest {

    private data class Observed(val sameParameters: Boolean, val agrees: Boolean)

    private fun observed(algorithm: String, keySize: Int, provider: String, agreement: String): Observed {
        val pairs = (KeyMaterialGenerator().generate(KeyRecipe.Pair(algorithm, keySize, provider, count = 2)) as KeyMaterial.Pairs).pairs
        assertEquals(2, pairs.size)
        val (first, second) = pairs
        val agrees = runCatching {
            KeyAgreement.getInstance(agreement, provider).apply { init(first.private); doPhase(second.public, true) }.generateSecret()
        }.isSuccess
        return Observed(parameters(first.public) == parameters(second.public), agrees)
    }

    private fun parameters(key: PublicKey): Any = when (key) {
        is DHPublicKey -> listOf(key.params.p, key.params.g)
        is ECPublicKey -> listOf(key.params.curve, key.params.generator, key.params.order, key.params.cofactor)
        is XECPublicKey -> (key.params as NamedParameterSpec).name
        else -> error("not an agreement key: ${key.javaClass.name}")
    }

    @Test
    fun sunJceDh2048ByKeySizeSharesItsGroupAndAgrees() {
        assertEquals(Observed(sameParameters = true, agrees = true), observed("DH", 2048, "SunJCE", "DH"))
    }

    @Test
    fun sunEcP256ByKeySizeSharesItsCurveAndAgrees() {
        assertEquals(Observed(sameParameters = true, agrees = true), observed("EC", 256, "SunEC", "ECDH"))
    }

    @Test
    fun bouncyCastleDh2048AndP256ByKeySize() = withBouncyCastle { name ->
        assertEquals(Observed(sameParameters = true, agrees = true), observed("DH", 2048, name, "DH"))
        assertEquals(Observed(sameParameters = true, agrees = true), observed("EC", 256, name, "ECDH"))
    }

    /** XDH's default curve is X25519: a pair sized 448 needs a peer on X448 too. */
    @Test
    fun xdh448PeersAreX448OnSunEcAndBouncyCastle() {
        assertEquals(Observed(sameParameters = true, agrees = true), observed("XDH", 448, "SunEC", "XDH"))
        withBouncyCastle { name -> assertEquals(Observed(sameParameters = true, agrees = true), observed("XDH", 448, name, "XDH")) }
    }

    private fun withBouncyCastle(block: (String) -> Unit) {
        val type = runCatching { Class.forName("org.bouncycastle.jce.provider.BouncyCastleProvider") }.getOrNull()
        assumeTrue("BouncyCastle is not on this classpath", type != null)
        val provider = type!!.getDeclaredConstructor().newInstance() as Provider
        val added = Security.getProvider(provider.name) == null && Security.addProvider(provider) != -1
        try {
            block(provider.name)
        } finally {
            if (added) Security.removeProvider(provider.name)
        }
    }
}
