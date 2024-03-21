package com.example.cryptobenchmark;

import com.example.cryptobenchmark.decrypt.assymmetric.AssymmetricDecrypt;
import com.example.cryptobenchmark.decrypt.symmetric.DecryptOperation;
import com.example.cryptobenchmark.encrypt.assymmetric.AssymmetricEncrypt;
import com.example.cryptobenchmark.encrypt.symmetric.EncryptOperation;
import com.example.cryptobenchmark.keygen.assymmetric.AssymmetricEncryptKeyGen;
import com.example.cryptobenchmark.misc.DeviceCryptoPrimitives;
import com.hunter.library.debug.HunterDebug;

import org.junit.Test;

import java.security.AlgorithmParameters;
import java.security.InvalidAlgorithmParameterException;
import java.security.KeyPair;
import java.security.NoSuchAlgorithmException;
import java.util.Map;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;

import static org.junit.Assert.assertNotNull;


public class MeasureAssymmetricAllTest extends MeasureTest{

    public static int KEY_LEN = keyLen; // keyLen;
    public static String CRYPTO_PROVIDER = MeasureTest.PROVIDER; // "AndroidOpenSSL"; //MeasureTest.provider;
    String[] params =  MeasureTest.INPUT_MESSAGES; //gen_random_workload(64, nTimes); // gen_random_workload(inputSize, nTimes);

    //@Test
@HunterDebug
    public void test_get_impl() {
        String[] algoList = {
                "RSA", "RSA/ECB/NOPADDING",
                "RSA/ECB/PKCS1PADDING", "RSA/ECB/OAEPPADDING", "RSA/ECB/OAEPWITHSHA-1ANDMGF1PADDING",
                "RSA/ECB/OAEPWITHSHA-224ANDMGF1PADDING",  "RSA/ECB/OAEPWITHSHA-256ANDMGF1PADDING",
                "RSA/ECB/OAEPWITHSHA-384ANDMGF1PADDING",  "RSA/ECB/OAEPWITHSHA-512ANDMGF1PADDING"
        };
        String[] providerList = {"AndroidOpenSSL", "AndroidKeyStoreBCWorkaround", "BC",
                "AndroidKeyStore", "" };

        for(String algo: algoList){
            for(String prov: providerList) {
                try{
                    Cipher md = prov.equals("") ? Cipher.getInstance(algo) : Cipher.getInstance(algo, prov);
                    String pevides =  md.getProvider().getName();
                    AlgorithmParameters apm  = md.getParameters();
                    System.out.println("algo: " + md.getAlgorithm());
                }catch (Exception e){
                    e.printStackTrace();
                }
            }
        }
    }

    public void sample_rsa() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "PKCS1PADDING";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        //encrypt(so, kp.getPublic(), params, PROVIDER, PADDING, MODE);
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, CRYPTO_PROVIDER, padding, mode);
        // OK
    }

    @Test
@HunterDebug
    
    public void test_RSA_ECB_PKCS1PADDING_AndroidOpenSSL() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "PKCS1PADDING",  provider = "AndroidOpenSSL";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
        //DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        //encrypt(so, kp.getPublic(), params, "AndroidOpenSSL", padding, mode);
        //OK
    }

    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPPADDING_AndroidOpenSSL() throws Exception{
        String algo = "RSA", mode = "ECB", padding = "OAEPPADDING",  provider = "AndroidOpenSSL";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
    }

    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPWITHSHA_1ANDMGF1PADDING_AndroidOpenSSL() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-1ANDMGF1PADDING",
                provider = "AndroidOpenSSL";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
    }


    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPWITHSHA_224ANDMGF1PADDING_AndroidOpenSSL() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-224ANDMGF1PADDING",
                provider = "AndroidOpenSSL";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider , padding, mode);
    }
    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPWITHSHA_256ANDMGF1PADDING_AndroidOpenSSL() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-256ANDMGF1PADDING",
                provider = "AndroidOpenSSL";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
    }

    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPWITHSHA_384ANDMGF1PADDING_AndroidOpenSSL() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-384ANDMGF1PADDING", provider = "AndroidOpenSSL";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
    }


    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPWITHSHA_512ANDMGF1PADDING_AndroidOpenSSL() throws Exception{
        // cannot be used with large block sizes (> 64?)
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-512ANDMGF1PADDING",
                provider = "AndroidOpenSSL";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
    }

    /*@Test
@HunterDebug
    public void test_rsa_xx() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        String algo = "RSA", mode = "ECB", padding = "OAEPPADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        assertNotNull(kp);
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        Map<String, Set<CryptoProvider>> m = dcp.getProvidersImplementingAlgorithm("EC");
        System.out.println(m);
    }*/

    @Test
@HunterDebug
    
    public void test_RSA_ECB_PKCS1PADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "PKCS1PADDING", provider = "AndroidKeyStoreBCWorkaround";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN, mode, padding);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
    }

    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPPADDING_AndroidKeyStoreBCWorkaround() throws Exception{
        String algo = "RSA", mode = "ECB", padding = "PKCS1PADDING", provider = "AndroidKeyStoreBCWorkaround";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN, mode, padding);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
    }

    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPWITHSHA_1ANDMGF1PADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-1ANDMGF1PADDING",
                provider = "AndroidKeyStoreBCWorkaround";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_rsakeyspec(KEY_LEN, mode, padding, provider);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        //encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
    }

    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPWITHSHA_224ANDMGF1PADDING() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-224ANDMGF1PADDING",
                provider = "AndroidKeyStoreBCWorkaround";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_rsakeyspec(KEY_LEN, mode, padding, provider);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
        // Only RSAKeyGenParameterSpec supported
    }

    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPWITHSHA_256ANDMGF1PADDING() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-256ANDMGF1PADDING",
                provider = "AndroidKeyStoreBCWorkaround";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_rsakeyspec(KEY_LEN, mode, padding, provider);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, provider, padding, mode);
        // Only RSAKeyGenParameterSpec supported
    }


    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPWITHSHA_384ANDMGF1PADDING() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-384ANDMGF1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, CRYPTO_PROVIDER, padding, mode);
    }


    @Test
@HunterDebug
    
    public void test_RSA_ECB_OAEPWITHSHA_512ANDMGF1PADDING() throws Exception{
        // cannot be used with large block sizes (> 64?)
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-512ANDMGF1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA(KEY_LEN);
        EncryptOperation so = AssymmetricEncrypt::encrypt_RSA;
        DecryptOperation deo = AssymmetricDecrypt::decrypt_RSA;
        encrypt_decrypt(so, deo, kp.getPublic(), kp.getPrivate(), params, CRYPTO_PROVIDER, padding, mode);
    }


}

