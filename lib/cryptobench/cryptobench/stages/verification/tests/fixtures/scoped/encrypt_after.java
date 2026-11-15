/** Seals with a fresh 12-byte IV prefixed to the ciphertext. */
public static byte[] encrypt(byte[] plain, SecretKey key) throws Exception {
    byte[] iv = new byte[12];
    new SecureRandom().nextBytes(iv);
    Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding", "AndroidOpenSSL");
    cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(128, iv));
    byte[] body = cipher.doFinal(plain);
    byte[] out = Arrays.copyOf(iv, iv.length + body.length);
    System.arraycopy(body, 0, out, iv.length, body.length);
    return out;
}
