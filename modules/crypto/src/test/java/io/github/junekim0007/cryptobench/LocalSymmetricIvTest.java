package io.github.junekim0007.cryptobench;

import io.github.junekim0007.cryptobench.crypto.primitive.cipher.symmetric.SymmetricDecrypt;
import io.github.junekim0007.cryptobench.crypto.primitive.cipher.symmetric.SymmetricEncrypt;

import org.junit.Test;

import java.util.Map;

import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

/**
 * Round trips on the desktop JVM (SunJCE) for every mode that takes an IV, plus ECB. Guards the IV
 * length and spec type; it does not exercise Conscrypt.
 */
public class LocalSymmetricIvTest {

    private static final String PROVIDER = "SunJCE";
    private static final String MESSAGE = "sixteen byte msg";

    private static SecretKey key(String algorithm, int bits) throws Exception {
        KeyGenerator generator = KeyGenerator.getInstance(algorithm);
        generator.init(bits);
        return generator.generateKey();
    }

    private static void aes(String mode, String padding) throws Exception {
        SecretKey k = key("AES", 128);
        Map.Entry<String, IvParameterSpec> encrypted = SymmetricEncrypt.encrypt_AES(MESSAGE, mode, padding, k, PROVIDER);
        assertNotNull("encrypt AES/" + mode, encrypted);
        assertEquals("AES/" + mode, MESSAGE,
                SymmetricDecrypt.decrypt_AES(encrypted.getKey(), mode, padding, k, PROVIDER, encrypted.getValue()));
    }

    private static void des(String mode, String padding) throws Exception {
        SecretKey k = key("DES", 56);
        Map.Entry<String, IvParameterSpec> encrypted = SymmetricEncrypt.encrypt_DES(MESSAGE, mode, padding, k, PROVIDER);
        assertNotNull("encrypt DES/" + mode, encrypted);
        assertEquals("DES/" + mode, MESSAGE,
                SymmetricDecrypt.decrypt_DES(encrypted.getKey(), mode, padding, k, PROVIDER, encrypted.getValue()));
    }

    private static void desede(String mode, String padding) throws Exception {
        SecretKey k = key("DESede", 168);
        Map.Entry<String, IvParameterSpec> encrypted = SymmetricEncrypt.encrypt_3DES(MESSAGE, mode, padding, k, PROVIDER);
        assertNotNull("encrypt DESede/" + mode, encrypted);
        assertEquals("DESede/" + mode, MESSAGE,
                SymmetricDecrypt.decrypt_3DES(encrypted.getKey(), mode, padding, k, PROVIDER, encrypted.getValue()));
    }

    @Test public void aesCbc() throws Exception { aes("CBC", "PKCS5Padding"); }
    @Test public void aesCtr() throws Exception { aes("CTR", "NoPadding"); }
    @Test public void aesOfb() throws Exception { aes("OFB", "NoPadding"); }
    @Test public void aesGcm() throws Exception { aes("GCM", "NoPadding"); }
    @Test public void aesEcb() throws Exception { aes("ECB", "PKCS5Padding"); }

    @Test public void desCbc() throws Exception { des("CBC", "PKCS5Padding"); }
    @Test public void desCtr() throws Exception { des("CTR", "NoPadding"); }
    @Test public void desOfb() throws Exception { des("OFB", "NoPadding"); }
    @Test public void desEcb() throws Exception { des("ECB", "PKCS5Padding"); }

    @Test public void desedeCbc() throws Exception { desede("CBC", "PKCS5Padding"); }
    @Test public void desedeEcb() throws Exception { desede("ECB", "PKCS5Padding"); }
}
