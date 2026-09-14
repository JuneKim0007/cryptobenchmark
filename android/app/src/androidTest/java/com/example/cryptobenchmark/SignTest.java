package com.example.cryptobenchmark;

import com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric.AssymmetricEncryptKeyGen;
import com.example.cryptobenchmark.environment.discovery.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.benchmark.preparation.workload.StringType;
import com.example.cryptobenchmark.crypto.primitive.signature.Sign;
import com.example.cryptobenchmark.crypto.primitive.signature.Verify;
import org.junit.Test;
import java.security.KeyPair;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

public class SignTest {

    public static final int DATA_LEN = 255;
    public static final int KEY_LEN = 1024;


    @Test
    public void test_ecdsa_sign() throws NoSuchAlgorithmException {
        String algo = "SHA256withECDSA";
        int keysize = 256;
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key_EC(keysize);
        String msg = (String) StringType.genRandomWithSize(DATA_LEN).getValue();
        String signature = Sign.sign(msg, algo, kp.getPrivate());
        assertNotNull(signature);
        assertTrue(Verify.verify(msg, signature, algo, kp.getPublic()));
    }

    @Test
    public void test_dsa_sign() throws NoSuchAlgorithmException {
        String algo = "DSA";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key(KEY_LEN, algo);
        String msg = (String) StringType.genRandomWithSize(DATA_LEN).getValue();
        String signature = Sign.sign(msg, algo, kp.getPrivate());
        assertNotNull(signature);
        assertTrue(Verify.verify(msg, signature, algo, kp.getPublic()));
    }

    @Test
    public void test_rsa_sign() throws NoSuchAlgorithmException {
        String algo = "SHA256withRSA";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key(KEY_LEN, "RSA");
        String msg = (String) StringType.genRandomWithSize(DATA_LEN).getValue();
        String signature = Sign.sign(msg, algo, kp.getPrivate());
        assertNotNull(signature);
        assertTrue(Verify.verify(msg, signature, algo, kp.getPublic()));
    }

    @Test
    public void test_sign_all() throws NoSuchAlgorithmException{
        List<String> algorithms = new ArrayList<>(Arrays.asList("DSA"));
        String msg = (String) StringType.genRandomWithSize(DATA_LEN).getValue();
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        for(String algorithm: algorithms){
            System.out.println(algorithm);
            Sign s = new Sign(dcp, Arrays.asList(algorithm));
            Verify v = new Verify(dcp, Arrays.asList(algorithm));
            KeyPair kp = AssymmetricEncryptKeyGen.gen_key(KEY_LEN, algorithm);
            List<String> signatures = s.sign_all(msg, kp.getPrivate());
            assertNotNull(signatures);
            assertTrue(v.verify_all(msg, signatures, kp.getPublic()));
        }
    }
}
