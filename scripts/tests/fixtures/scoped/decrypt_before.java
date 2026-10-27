public static byte[] decrypt(byte[] sealed, SecretKey key) throws Exception {
    Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
    cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, sealed, 0, 12));
    return cipher.doFinal(sealed, 12, sealed.length - 12);
}
