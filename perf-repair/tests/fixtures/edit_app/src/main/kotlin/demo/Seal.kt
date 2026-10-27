package demo

import java.security.PrivateKey
import java.security.PublicKey
import javax.crypto.Cipher

object Seal {
    fun wrap(key: PublicKey, data: ByteArray): ByteArray {
        val c: Cipher = Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding")
        c.init(Cipher.ENCRYPT_MODE, key)
        return c.doFinal(data)
    }

    fun unwrap(key: PrivateKey, data: ByteArray): ByteArray {
        val c = Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding", "Slow").apply {
            init(Cipher.DECRYPT_MODE, key)
        }
        return c.doFinal(data)
    }

    fun template(data: ByteArray, mode: String): ByteArray {
        val c = Cipher.getInstance(
            "AES/$mode/NoPadding",
            "Slow"
        )
        c.init(Cipher.ENCRYPT_MODE, secret)
        return data.map { b -> b }.toByteArray() + c.doFinal(data)
    }
}
