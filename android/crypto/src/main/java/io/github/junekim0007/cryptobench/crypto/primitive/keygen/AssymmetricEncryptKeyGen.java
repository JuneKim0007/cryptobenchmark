package io.github.junekim0007.cryptobench.crypto.primitive.keygen;

import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;

import java.security.InvalidAlgorithmParameterException;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.NoSuchAlgorithmException;
import java.security.spec.RSAKeyGenParameterSpec;
public class AssymmetricEncryptKeyGen {

    public static KeyPair  gen_key_RSA(int keylen) throws NoSuchAlgorithmException {
        KeyPairGenerator keyGen = KeyPairGenerator.getInstance("RSA");
        RSAKeyGenParameterSpec keyGenSpec;
        keyGenSpec = new RSAKeyGenParameterSpec(
                keylen, RSAKeyGenParameterSpec.F0);
        try {
            keyGen.initialize(keyGenSpec);
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
        }
        return keyGen.generateKeyPair();
    }

    public static KeyPair gen_key_RSA(int keylen, String mode, String padding) throws NoSuchAlgorithmException, InvalidAlgorithmParameterException {
        KeyPairGenerator keyPairGenerator = java.security.KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_RSA);
        KeyGenParameterSpec parameterSpec = new KeyGenParameterSpec.Builder("cryptobenchmark1",
                KeyProperties.PURPOSE_SIGN | KeyProperties.PURPOSE_DECRYPT| KeyProperties.PURPOSE_ENCRYPT )
                .setUserAuthenticationRequired(false)
                .setBlockModes(mode)
                //.setDigests(KeyProperties.DIGEST_SHA256)
                .setEncryptionPaddings(padding)
                .setRandomizedEncryptionRequired(false)
                .setKeySize(keylen)
                .build();
        keyPairGenerator.initialize(parameterSpec);
        return keyPairGenerator.genKeyPair();
    }

    public static KeyPair gen_key(int keylen, String algo) throws NoSuchAlgorithmException {
        KeyPairGenerator keyPairGenerator = java.security.KeyPairGenerator.getInstance(algo);
        keyPairGenerator.initialize(keylen);
        return keyPairGenerator.genKeyPair();
    }

    public static KeyPair gen_key_rsakeyspec(int keylen, String mode, String padding, String provider) throws Exception {
        RSAKeyGenParameterSpec spec = new RSAKeyGenParameterSpec(keylen, RSAKeyGenParameterSpec.F4);
        String algoDefinition = (mode.equals("") || padding.equals("")) ? "RSA" : String.format("RSA/%s/%s", mode, padding);
        KeyPairGenerator kpg = KeyPairGenerator.getInstance(algoDefinition, provider);
        kpg.initialize(spec);
        return kpg.generateKeyPair();
    }

}
