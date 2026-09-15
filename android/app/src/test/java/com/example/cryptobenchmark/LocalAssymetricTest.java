package com.example.cryptobenchmark;

import com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric.AssymmetricDecrypt;
import com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric.AssymmetricEncrypt;
import com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric.AssymmetricEncryptKeyGen;
import com.example.cryptobenchmark.benchmark.preparation.workload.StringType;

import org.junit.Test;

import java.security.InvalidAlgorithmParameterException;
import java.security.KeyPair;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.util.Map;

import javax.crypto.spec.IvParameterSpec;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

public class LocalAssymetricTest {

    @Test
    public void test_sample_rsa() throws InvalidAlgorithmParameterException, NoSuchAlgorithmException, NoSuchProviderException {
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(128);
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key(1024, "RSA");
        assertNotNull(kp);
        String msg = (String) StringType.genRandomWithSize(128).getValue();
        Map.Entry<String, IvParameterSpec> res = AssymmetricEncrypt.encrypt_RSA(msg, "ECB", "NOPADDING", kp.getPublic(), "SunJCE");
        assertNotNull(res);
        String decrypted_plaintext = AssymmetricDecrypt.decrypt_RSA(res.getKey(), "ECB", "NOPADDING", kp.getPrivate(), "SunJCE", res.getValue());
        System.out.println(msg);
        System.out.println(decrypted_plaintext);
        assertEquals(msg, decrypted_plaintext);
    }

}