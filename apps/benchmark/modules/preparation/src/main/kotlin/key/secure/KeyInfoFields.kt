package io.github.junekim0007.cryptobench.preparation.key.secure

import io.github.junekim0007.cryptobench.jca.reflect.Reflect
import java.security.Key
import java.security.KeyFactory
import java.security.GeneralSecurityException
import java.security.KeyPair
import java.security.Security
import java.security.spec.KeySpec
import javax.crypto.SecretKey
import javax.crypto.SecretKeyFactory

/** What the keystore says of a key it made, read through the provider's own factory as android.security.keystore.KeyInfo: where it lives and its size. */
internal object KeyInfoFields {

    const val SECURITY_LEVEL = "securityLevel"
    const val KEY_BITS = "keyBits"
    private const val KEY_INFO = "android.security.keystore.KeyInfo"
    private const val LEVEL_PREFIX = "SECURITY_LEVEL_"
    private val LABELS = mapOf("TRUSTED_ENVIRONMENT" to "TEE", "STRONGBOX" to "STRONGBOX", "SOFTWARE" to "SOFTWARE")
    private const val UNKNOWN = "UNKNOWN"
    private const val KEY_FACTORY = "KeyFactory"

    fun of(result: Any?, provider: String): Map<String, Any> {
        val key: Key = (result as? KeyPair)?.private ?: result as? Key ?: throw IllegalStateException("no key to read: ${result?.javaClass?.name}")
        val infoClass = Class.forName(KEY_INFO)
        val info: KeySpec = if (key is SecretKey) SecretKeyFactory.getInstance(key.algorithm, provider).getKeySpec(key, infoClass) else pairInfo(key, provider, infoClass)
        return linkedMapOf(SECURITY_LEVEL to level(info, infoClass), KEY_BITS to infoClass.getMethod("getKeySize").invoke(info) as Int)
    }

    // the factory of the key's own algorithm, else the first of the provider's factories that reads it (a key named EdDSA, a factory named otherwise)
    @Suppress("UNCHECKED_CAST")
    private fun pairInfo(key: Key, provider: String, infoClass: Class<*>): KeySpec {
        val names = listOf(key.algorithm) + Security.getProvider(provider).services.filter { it.type == KEY_FACTORY }.map { it.algorithm }
        var refused: Exception? = null
        for (name in names.distinct()) {
            try {
                return KeyFactory.getInstance(name, provider).getKeySpec(key, infoClass as Class<KeySpec>)
            } catch (failure: GeneralSecurityException) {
                refused = refused ?: failure
            }
        }
        throw refused ?: IllegalStateException("$provider registers no $KEY_FACTORY")
    }

    // API 31 names the level; below it only inside-secure-hardware is known, so true cannot tell TEE from StrongBox
    private fun level(info: Any, infoClass: Class<*>): String {
        val method = try { infoClass.getMethod("getSecurityLevel") } catch (absent: NoSuchMethodException) { null }
            ?: return if (infoClass.getMethod("isInsideSecureHardware").invoke(info) as Boolean) UNKNOWN else LABELS.getValue("SOFTWARE")
        val value = Reflect.invoke(method, info) as Int
        val name = Class.forName(KeystoreSpec.PROPERTIES).fields.firstOrNull { it.name.startsWith(LEVEL_PREFIX) && it.getInt(null) == value }?.name
        return LABELS[name?.removePrefix(LEVEL_PREFIX)] ?: UNKNOWN
    }
}
