package demo

import android.content.SharedPreferences
import java.security.KeyStore
import javax.crypto.*
import javax.crypto.spec.SecretKeySpec

const val MODE = "GCM"
private const val TRANSFORM = "AES/" + MODE +
    "/NoPadding"

object Names {
    val DIGEST = "SHA256"
}

/* Cipher.getInstance("AES/GCM/NoPadding") /* nested */ still a comment */
class Vault(private val prefs: SharedPreferences) {
    val eager = Cipher.getInstance(TRANSFORM)

    fun seal(data: ByteArray) {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val c = Cipher.getInstance(
            TRANSFORM
        )
        c.init(Cipher.ENCRYPT_MODE, ks.getKey("k", null))
        prefs.edit().putString("blob", c.doFinal(data).toString()).apply()
    }

    fun digest(b: ByteArray): ByteArray =
        java.security.MessageDigest.getInstance(Names.DIGEST)
            .digest(b)

    fun tag(key: ByteArray, b: ByteArray): ByteArray {
        val m = Mac.getInstance("HmacSHA256")
        m.init(SecretKeySpec(key, "HmacSHA256"))
        return m.doFinal(b)
    }

    fun later(): () -> Cipher {
        val make = { Cipher.getInstance("AES/GCM/NoPadding") }
        return make
    }

    fun templated(mode: String) = Cipher.getInstance("AES/$mode/NoPadding")
}
