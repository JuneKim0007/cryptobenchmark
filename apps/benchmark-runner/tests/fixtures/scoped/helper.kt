fun seal(data: ByteArray): ByteArray = cipherFor(KEY_ALIAS).doFinal(data)
