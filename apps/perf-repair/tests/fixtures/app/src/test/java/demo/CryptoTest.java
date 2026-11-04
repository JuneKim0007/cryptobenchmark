package demo;

import javax.crypto.Cipher;

class CryptoTest {
    void seals() throws Exception {
        Cipher.getInstance("AES/GCM/NoPadding");
    }
}
