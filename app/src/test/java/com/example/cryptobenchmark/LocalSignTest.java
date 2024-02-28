package com.example.cryptobenchmark;

import com.example.cryptobenchmark.keygen.assymmetric.AssymmetricEncryptKeyGen;
import com.example.cryptobenchmark.misc.CryptoProvider;
import com.example.cryptobenchmark.misc.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.misc.datatypes.StringType;
import com.example.cryptobenchmark.sign.Sign;
import com.example.cryptobenchmark.verify.Verify;

import org.junit.Test;

import java.security.InvalidAlgorithmParameterException;
import java.security.KeyPair;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

public class LocalSignTest {

    public static final int DATA_LEN = 128;
    public static final int KEY_LEN = 512;

    public void test_get_sign_impls() {
        String algo = "ECDSA";
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        Map<String, Set<CryptoProvider>> cps = de.getProvidersImplementingAlgorithm(algo);
        Sign s = new Sign(de);
        System.out.println(s);
    }

    @Test
    public void test_sign_local() throws NoSuchAlgorithmException{
        String algo = "SHA256withRSA";
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key(1024, "RSA");
        String msg = (String) StringType.genRandomWithSize(255).getValue();
        String signature = Sign.sign(msg, algo, kp.getPrivate());
        //byte[] signature = Sign.sign_b(msg, algo, kp.getPrivate());
        assertNotNull(signature);
        assertTrue(Verify.verify(msg, signature, algo, kp.getPublic()));
    }

    @Test    
    public void test_sign_local_all() throws NoSuchAlgorithmException{
        List<String> algorithms = new ArrayList<>(Arrays.asList("DSA"));
        KeyPair kp = AssymmetricEncryptKeyGen.gen_key(1024, "DSA");
        String msg = (String) StringType.genRandomWithSize(DATA_LEN).getValue();
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        Sign s = new Sign(dcp, algorithms);
        Verify v = new Verify(dcp, algorithms);
        List<String> signatures = s.sign_all(msg, kp.getPrivate());
        assertNotNull(signatures);
        assertTrue(v.verify_all(msg, signatures, kp.getPublic()));
    }
}
