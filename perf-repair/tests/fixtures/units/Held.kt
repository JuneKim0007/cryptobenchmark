package demo

import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey

class Held {
    private var key: SecretKey? = null

    private fun fresh(): SecretKey {
        val g = KeyGenerator.getInstance("ALG-D") // site: kt_generator
        return g.generateKey()
    }

    fun reset() {
        key = KeyGenerator.getInstance("ALG-D").generateKey() // site: kt_field_generator
    }

    fun helperKey(data: ByteArray): ByteArray {
        val made = fresh()
        val c = Cipher.getInstance("ALG-D/Y") // site: kt_helper
        c.init(Cipher.ENCRYPT_MODE, made)
        return c.doFinal(data)
    }

    fun heldKey(data: ByteArray): ByteArray {
        val c = Cipher.getInstance("ALG-D/Y") // site: kt_held
        c.init(Cipher.DECRYPT_MODE, key)
        return c.doFinal(data)
    }

    fun wrapIt(data: SecretKey): ByteArray {
        val c = Cipher.getInstance("ALG-E") // site: kt_wrap
        c.init(Cipher.WRAP_MODE, key)
        return c.wrap(data)
    }
}
