import java.security.MessageDigest
import javax.crypto.Cipher

class Seal(private val key: java.security.Key) {
    private val digest by lazy { MessageDigest.getInstance("ALG-B") } // site: lazy_field

    fun open(data: ByteArray): ByteArray {
        val c = Cipher.getInstance("ALG-A").apply { init(Cipher.DECRYPT_MODE, key) } // site: apply
        return c.doFinal(data)
    }

    fun sum(data: ByteArray) = digest.digest(data)

    fun chain(data: ByteArray): ByteArray = MessageDigest.getInstance("ALG-B").digest(data) // site: chain

    fun with(data: ByteArray): ByteArray = with(MessageDigest.getInstance("ALG-B")) { digest(data) } // site: with

    fun later(data: ByteArray): () -> ByteArray {
        val c = Cipher.getInstance("ALG-A") // site: deferred
        c.init(Cipher.ENCRYPT_MODE, key)
        return { c.doFinal(data) }
    }

    fun unused() {
        val c = Cipher.getInstance("ALG-A") // site: no_real_use
    }

    fun unknownEngine() {
        val e = Unlisted.getInstance("X") // site: engine_unknown
        e.go()
    }
}
