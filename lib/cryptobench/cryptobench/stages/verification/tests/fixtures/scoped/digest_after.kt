private fun digest(data: ByteArray): ByteArray = MessageDigest.getInstance("SHA-256", "AndroidOpenSSL").digest(data)
