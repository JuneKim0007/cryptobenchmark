import javax.crypto.Mac

class Ledger(private val prefs: Prefs) {
    private fun literalKey() = byteArrayOf(1, 2)

    fun sealed(data: ByteArray): ByteArray {
        val m = Mac.getInstance("ALG-B") // site: expression_body
        m.init(wrap(literalKey()))
        return m.doFinal(data)
    }

    private fun secret(): java.security.Key = prefs.fetch("a")

    fun opaque(data: ByteArray): ByteArray {
        val m = Mac.getInstance("ALG-B") // site: returned_open
        m.init(secret())
        return m.doFinal(data)
    }
}
