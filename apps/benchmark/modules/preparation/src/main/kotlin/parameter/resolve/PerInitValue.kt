package io.github.junekim0007.cryptobench.preparation.parameter.resolve

import java.security.GeneralSecurityException
import java.security.Key
import javax.crypto.Cipher

/** Whether a cipher's IvParameterSpec value is an IV: false only when a fresh instance fills in the same value on two inits. */
internal object PerInitValue {

    // A constant the provider fills in (a key-wrap integrity check value) is not an IV; a refusal to choose means the caller must supply one.
    fun isIv(cipher: Cipher, encryptionKey: Key): Boolean {
        val fresh = Cipher.getInstance(cipher.algorithm, cipher.provider)
        val first = chosen(fresh, encryptionKey) ?: return true
        val second = chosen(fresh, encryptionKey) ?: return true
        return !first.contentEquals(second)
    }

    private fun chosen(cipher: Cipher, key: Key): ByteArray? = try {
        cipher.init(Cipher.ENCRYPT_MODE, key)
        cipher.iv
    } catch (refused: GeneralSecurityException) {
        null
    }
}
