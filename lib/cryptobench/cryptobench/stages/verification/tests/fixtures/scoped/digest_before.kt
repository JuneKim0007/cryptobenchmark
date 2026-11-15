private fun digest(data: ByteArray): ByteArray = MessageDigest.getInstance("SHA-256").digest(data)
