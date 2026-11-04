package demo

import java.security.PrivateKey
import java.security.PublicKey
import java.security.Signature
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.Mac
import javax.crypto.SecretKey

class Delegate(private val key: SecretKey) {
    private val mac: Mac by lazy {
        Mac.getInstance("ALG-M").apply { init(key) } // site: k_lazy_delegate
    }

    fun tag(data: ByteArray): ByteArray = mac.doFinal(data)
}

class NullCache(private val key: SecretKey) {
    private var cache: Cipher? = null

    fun cached(data: ByteArray): ByteArray {
        val c = cache ?: Cipher.getInstance("ALG-A/X").also { // site: k_lazy_null
            it.init(Cipher.ENCRYPT_MODE, key)
            cache = it
        }
        return c.doFinal(data)
    }
}

class Reinit(private val key: SecretKey) {
    private val held: Cipher = Cipher.getInstance("ALG-A/X") // site: k_reinit

    fun again(data: ByteArray): ByteArray {
        held.init(Cipher.ENCRYPT_MODE, key)
        return held.doFinal(data)
    }
}

object PerCall {
    fun once(data: ByteArray, key: SecretKey): ByteArray {
        val c = Cipher.getInstance("ALG-A/X") // site: k_local
        c.init(Cipher.ENCRYPT_MODE, key)
        return c.doFinal(data)
    }

    fun applied(data: ByteArray, key: SecretKey): ByteArray {
        val c = Cipher.getInstance("ALG-A/X").apply { init(Cipher.ENCRYPT_MODE, key) } // site: k_apply
        return c.doFinal(data)
    }

    fun make(key: SecretKey): Cipher {
        val c = Cipher.getInstance("ALG-A/X") // site: k_escape
        c.init(Cipher.DECRYPT_MODE, key)
        return c
    }
}

class Notary {
    fun sign(data: ByteArray, priv: PrivateKey): ByteArray {
        val s = Signature.getInstance("ALG-S") // site: k_sign
        s.initSign(priv)
        s.update(data)
        return s.sign()
    }

    fun verify(data: ByteArray, sig: ByteArray, pub: PublicKey): Boolean {
        val s = Signature.getInstance("ALG-S") // site: k_verify
        s.initVerify(pub)
        s.update(data)
        return s.verify(sig)
    }
}

class Minted {
    private var made: SecretKey? = null

    fun reset() {
        made = KeyGenerator.getInstance("ALG-C").generateKey() // site: k_generator
    }

    fun sealMade(data: ByteArray): ByteArray {
        val c = Cipher.getInstance("ALG-C/Z") // site: k_seal
        c.init(Cipher.ENCRYPT_MODE, made)
        return c.doFinal(data)
    }

    fun openMade(data: ByteArray): ByteArray {
        val c = Cipher.getInstance("ALG-C/Z") // site: k_open
        c.init(Cipher.DECRYPT_MODE, made)
        return c.doFinal(data)
    }
}
