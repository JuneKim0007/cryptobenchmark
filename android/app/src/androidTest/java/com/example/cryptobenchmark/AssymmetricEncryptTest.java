package com.example.cryptobenchmark;

import androidx.test.runner.AndroidJUnit4;

import com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric.AssymmetricDecrypt;
import com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric.AssymmetricEncrypt;
import com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric.AssymmetricEncryptKeyGen;

import com.example.cryptobenchmark.setup.CryptoProvider;
import com.example.cryptobenchmark.setup.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.bench.fixture.workload.StringType;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.security.InvalidAlgorithmParameterException;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.util.Map;
import java.util.Set;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import com.hunter.library.debug.HunterDebug;

/**
 * Instrumented test, which will execute on an Android device.
 *
 * @see <a href="http://d.android.com/tools/testing">Testing documentation</a>
 */
@RunWith(AndroidJUnit4.class)
public class AssymmetricEncryptTest {

    public static int KEY_LEN = 2048; // 1024 -> 117, 2048 -> 245
    public static int PLAINTEXT_LEN = 120;
    public static String RSA_MODE = "ECB";
    public static String PROVIDER = "AndroidKeyStoreBCWorkaround";


    @Test
    @HunterDebug
    public void test_sample_rsa() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        String algo = "RSA", mode = "ECB", padding = "PKCS1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(2048, mode, padding);
        assertNotNull(kp);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        AssymmetricEncrypt ae = new AssymmetricEncrypt(dcp);
        AssymmetricDecrypt ad = new AssymmetricDecrypt(dcp);
        String msg = (String) StringType.genRandomWithSize(PLAINTEXT_LEN).getValue();
        Map.Entry<String, IvParameterSpec> res = ae.encrypt_RSA(msg, mode, padding, kp.getPublic(), "AndroidKeyStoreBCWorkaround");
        assertNotNull(res);
        String decrypted_plaintext = ad.decrypt_RSA(res.getKey(), mode, padding, kp.getPrivate(), "AndroidKeyStoreBCWorkaround", res.getValue());
        assertEquals(msg, decrypted_plaintext);
    }

    @Test
    @HunterDebug
    public void test_rsa_PKCS1PADDING() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        String algo = "RSA", mode = "ECB", padding = "PKCS1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN, mode, padding);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        AssymmetricEncrypt ae = new AssymmetricEncrypt(dcp);
        AssymmetricDecrypt ad = new AssymmetricDecrypt(dcp);
        String msg = (String) StringType.genRandomWithSize(PLAINTEXT_LEN).getValue();
        Map.Entry<String, IvParameterSpec> res = ae.encrypt_RSA(msg, mode, padding, kp.getPublic(), "AndroidKeyStoreBCWorkaround");
        assertNotNull(res);
        String decrypted_plaintext = ad.decrypt_RSA(res.getKey(), mode, padding, kp.getPrivate(), "AndroidKeyStoreBCWorkaround", res.getValue());
        assertEquals(msg, decrypted_plaintext);
    }

    @Test
    @HunterDebug
    public void test_rsa_OAEPPADDING() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        String algo = "RSA", mode = "ECB", padding = "OAEPPADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN, mode, padding);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        AssymmetricEncrypt ae = new AssymmetricEncrypt(dcp);
        AssymmetricDecrypt ad = new AssymmetricDecrypt(dcp);
        String msg = (String) StringType.genRandomWithSize(PLAINTEXT_LEN).getValue();
        Map.Entry<String, IvParameterSpec> res = ae.encrypt_RSA(msg, mode, padding, kp.getPublic(), "AndroidKeyStoreBCWorkaround");
        assertNotNull(res);
        String decrypted_plaintext = ad.decrypt_RSA(res.getKey(), mode, padding, kp.getPrivate(), "AndroidKeyStoreBCWorkaround", res.getValue());
        //assertEquals(msg, decrypted_plaintext);
        System.out.println(msg);
        System.out.println(res.getKey());
        //System.out.println(decrypted_plaintext);
    }

    @Test
    @HunterDebug
    public void test_rsa_OAEPWITHSHA_1ANDMGF1PADDING() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-1ANDMGF1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN, mode, padding);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        AssymmetricEncrypt ae = new AssymmetricEncrypt(dcp);
        AssymmetricDecrypt ad = new AssymmetricDecrypt(dcp);
        String msg = (String) StringType.genRandomWithSize(PLAINTEXT_LEN).getValue();
        Map.Entry<String, IvParameterSpec> res = ae.encrypt_RSA(msg, mode, padding, kp.getPublic(), "AndroidKeyStoreBCWorkaround");
        assertNotNull(res);
        String decrypted_plaintext = ad.decrypt_RSA(res.getKey(), mode, padding, kp.getPrivate(), "AndroidKeyStoreBCWorkaround", res.getValue());
        assertEquals(msg, decrypted_plaintext);
    }



    @Test
    public void test_rsa_OAEPWITHSHA_224ANDMGF1PADDING() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-224ANDMGF1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN, mode, padding);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        AssymmetricEncrypt ae = new AssymmetricEncrypt(dcp);
        AssymmetricDecrypt ad = new AssymmetricDecrypt(dcp);
        String msg = (String) StringType.genRandomWithSize(PLAINTEXT_LEN).getValue();
        Map.Entry<String, IvParameterSpec> res = ae.encrypt_RSA(msg, mode, padding, kp.getPublic(), "AndroidKeyStoreBCWorkaround");
        assertNotNull(res);
        String decrypted_plaintext = ad.decrypt_RSA(res.getKey(), mode, padding, kp.getPrivate(), "AndroidKeyStoreBCWorkaround", res.getValue());
        assertEquals(msg, decrypted_plaintext);
    }
    @Test
    public void test_rsa_OAEPWITHSHA_256ANDMGF1PADDING() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-256ANDMGF1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN, mode, padding);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        AssymmetricEncrypt ae = new AssymmetricEncrypt(dcp);
        AssymmetricDecrypt ad = new AssymmetricDecrypt(dcp);
        String msg = (String) StringType.genRandomWithSize(PLAINTEXT_LEN).getValue();
        Map.Entry<String, IvParameterSpec> res = ae.encrypt_RSA(msg, mode, padding, kp.getPublic(), "AndroidKeyStoreBCWorkaround");
        assertNotNull(res);
        String decrypted_plaintext = ad.decrypt_RSA(res.getKey(), mode, padding, kp.getPrivate(), "AndroidKeyStoreBCWorkaround", res.getValue());
        assertEquals(msg, decrypted_plaintext);
    }

    @Test
    public void test_rsa_OAEPWITHSHA_384ANDMGF1PADDING() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-384ANDMGF1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN, mode, padding);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        AssymmetricEncrypt ae = new AssymmetricEncrypt(dcp);
        AssymmetricDecrypt ad = new AssymmetricDecrypt(dcp);
        String msg = (String) StringType.genRandomWithSize(PLAINTEXT_LEN).getValue();
        Map.Entry<String, IvParameterSpec> res = ae.encrypt_RSA(msg, mode, padding, kp.getPublic(), "AndroidKeyStoreBCWorkaround");
        assertNotNull(res);
        String decrypted_plaintext = ad.decrypt_RSA(res.getKey(), mode, padding, kp.getPrivate(), "AndroidKeyStoreBCWorkaround", res.getValue());
        assertEquals(msg, decrypted_plaintext);
    }

    @Test
    public void test_rsa_OAEPWITHSHA_512ANDMGF1PADDING() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-512ANDMGF1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN, mode, padding);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        AssymmetricEncrypt ae = new AssymmetricEncrypt(dcp);
        AssymmetricDecrypt ad = new AssymmetricDecrypt(dcp);
        String msg = (String) StringType.genRandomWithSize(PLAINTEXT_LEN).getValue();
        Map.Entry<String, IvParameterSpec> res = ae.encrypt_RSA(msg, mode, padding, kp.getPublic(), "AndroidOpenSSL");
        assertNotNull(res);
        String decrypted_plaintext = ad.decrypt_RSA(res.getKey(), mode, padding, kp.getPrivate(), "AndroidOpenSSL", res.getValue());
        assertEquals(msg, decrypted_plaintext);
    }

    @Test
    public void test_rsa_xx() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        String algo = "RSA", mode = "ECB", padding = "OAEPPADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        assertNotNull(kp);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        Map<String, Set<CryptoProvider>> m = dcp.getProvidersImplementingAlgorithm("EC");
        System.out.println(m);
    }

    @Test
    public void test_ec(){
        // does not work without SC
        String msg = (String) StringType.genRandomWithSize(PLAINTEXT_LEN).getValue();
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_EC(224);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        AssymmetricEncrypt ae = new AssymmetricEncrypt(dcp);
        Map.Entry<String, IvParameterSpec> res = ae.encryptEC(msg, kp.getPublic(), "BC");
        System.out.println(res);
    }

}