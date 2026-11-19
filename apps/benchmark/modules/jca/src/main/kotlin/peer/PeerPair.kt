package io.github.junekim0007.cryptobench.jca.peer

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.jca.reflect.Reflect
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.PublicKey
import java.security.SecureRandom
import java.security.interfaces.ECKey
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.interfaces.DHKey

/** The second key pair of an agreement, on the first one's curve or group, so the two can agree; discovery's and preparation's one way. */
object PeerPair {

    fun of(own: KeyPair, generator: KeyPairGenerator, random: SecureRandom? = null): KeyPair {
        val shared = when (val public = own.public) {
            is ECKey -> public.params
            is DHKey -> public.params
            // an XEC default may already be the curve: some providers refuse a named spec, others refuse to generate uninitialized (BC)
            else -> return xec(public)?.let { curve ->
                Attempt.of { generator.generateKeyPair() }.getOrNull()?.takeIf { name(xec(it.public)) == name(curve) }
                    ?: generator.initialized(curve, random).generateKeyPair()
            } ?: generator.generateKeyPair()
        }
        return generator.initialized(shared, random).generateKeyPair()
    }

    private fun KeyPairGenerator.initialized(spec: AlgorithmParameterSpec, random: SecureRandom?) =
        apply { if (random == null) initialize(spec) else initialize(spec, random) }

    // XECKey.getParams (API 33, JDK 11) by name: absent on an older runtime or a key of another kind
    private fun xec(key: PublicKey): AlgorithmParameterSpec? {
        val type = XEC_KEY ?: return null
        if (!type.isInstance(key)) return null
        return Reflect.invoke(type.getMethod("getParams"), key) as? AlgorithmParameterSpec
    }

    // NamedParameterSpec has no equals: its curve name is the identity
    private fun name(spec: AlgorithmParameterSpec?): String? =
        spec?.let { Attempt.of { Reflect.invoke(it.javaClass.getMethod("getName"), it) as? String }.getOrNull() }

    private val XEC_KEY: Class<*>? = Attempt.of { Class.forName("java.security.interfaces.XECKey") }.getOrNull()
}
