package com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric;

import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;

import java.security.InvalidAlgorithmParameterException;
import java.security.KeyFactory;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.security.SecureRandom;
import java.security.spec.DSAParameterSpec;
import java.security.spec.RSAKeyGenParameterSpec;
public class AssymmetricEncryptKeyGen {

    public static KeyPair  gen_key_RSA_AndroidKeyStore(int keylen) throws NoSuchProviderException, NoSuchAlgorithmException, InvalidAlgorithmParameterException {
        KeyPairGenerator keyPairGenerator = java.security.KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_RSA, "AndroidKeyStore");

        //We are creating the key pair with sign and verify purposes
        KeyGenParameterSpec parameterSpec = new KeyGenParameterSpec.Builder("cryptobenchmark",
                KeyProperties.PURPOSE_SIGN | KeyProperties.PURPOSE_DECRYPT | KeyProperties.PURPOSE_ENCRYPT)
                .setUserAuthenticationRequired(false)
                .setBlockModes(KeyProperties.BLOCK_MODE_ECB)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_RSA_PKCS1)
                .setRandomizedEncryptionRequired(false)
                .setKeySize(keylen)
                .build();

        //Initialization of key generator with the parameters we have specified above
        keyPairGenerator.initialize(parameterSpec);
        //Generates the key pair
        return keyPairGenerator.genKeyPair();
    }
    /*
    public static KeyPair  gen_key_RSA(int keylen) throws NoSuchAlgorithmException {
        KeyPairGenerator keyPairGenerator = java.security.KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_RSA);
        keyPairGenerator.initialize(keylen);
        //We are creating the key pair with sign and verify purposes
        KeyGenParameterSpec parameterSpec = new KeyGenParameterSpec.Builder("cryptobenchmark",
                KeyProperties.PURPOSE_SIGN | KeyProperties.PURPOSE_DECRYPT )
                .setUserAuthenticationRequired(false)
                .setBlockModes(KeyProperties.BLOCK_MODE_ECB)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(false)
                .setKeySize(keylen)
                .build();

        //Initialization of key generator with the parameters we have specified above
        keyPairGenerator.initialize(parameterSpec);
        //Generates the key pair
        return keyPairGenerator.genKeyPair();
    }*/
    public static KeyPair dummy_RSA_key(int len){
        KeyPairGenerator keyPairGenerator = null;
        try {
            keyPairGenerator = KeyPairGenerator.getInstance("RSA");
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        keyPairGenerator.initialize(len);
        return keyPairGenerator.generateKeyPair();

    }

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

    public static KeyPair gen_key_RSA_AndroidKeyStore(int keylen, String mode, String padding) throws Exception {
        KeyPairGenerator keyPairGenerator = java.security.KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_RSA, "AndroidKeyStore");
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

    public static KeyPair dumb_gen_key_RSA_AndroidKeyStore(int keylen, String mode) throws Exception {
        KeyPairGenerator keyPairGenerator = java.security.KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_RSA, "AndroidKeyStore");
        KeyGenParameterSpec parameterSpec = new KeyGenParameterSpec.Builder("cryptobenchmark1",
                KeyProperties.PURPOSE_SIGN | KeyProperties.PURPOSE_DECRYPT| KeyProperties.PURPOSE_ENCRYPT )
                .setUserAuthenticationRequired(false)
                .setBlockModes(mode)
                .setRandomizedEncryptionRequired(false)
                .setKeySize(keylen)
                .build();
        keyPairGenerator.initialize(parameterSpec);
        return keyPairGenerator.genKeyPair();
    }

    public static KeyPair gen_key(int keylen, String algo) throws NoSuchAlgorithmException {
        KeyPairGenerator keyPairGenerator = java.security.KeyPairGenerator.getInstance(algo);
        keyPairGenerator.initialize(keylen);
        /*
        //We are creating the key pair with sign and verify purposes
        KeyGenParameterSpec parameterSpec = new KeyGenParameterSpec.Builder("cryptobenchmark",
                KeyProperties.PURPOSE_SIGN | KeyProperties.PURPOSE_DECRYPT )
                .setUserAuthenticationRequired(false)
                .setBlockModes(KeyProperties.BLOCK_MODE_ECB)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(false)
                .setKeySize(keylen)
                .build();

        //Initialization of key generator with the parameters we have specified above
        keyPairGenerator.initialize(parameterSpec);*/
        //Generates the key pair
        return keyPairGenerator.genKeyPair();
    }

    public static KeyPair gen_rsa_key_for_provider(int keylen, String provider) throws Exception {
        KeyPairGenerator keyPairGenerator = java.security.KeyPairGenerator.getInstance("RSA", provider);
        keyPairGenerator.initialize(keylen);
        /*
        //We are creating the key pair with sign and verify purposes
        KeyGenParameterSpec parameterSpec = new KeyGenParameterSpec.Builder("cryptobenchmark",
                KeyProperties.PURPOSE_SIGN | KeyProperties.PURPOSE_DECRYPT )
                .setUserAuthenticationRequired(false)
                .setBlockModes(KeyProperties.BLOCK_MODE_ECB)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(false)
                .setKeySize(keylen)
                .build();

        //Initialization of key generator with the parameters we have specified above
        keyPairGenerator.initialize(parameterSpec);*/
        //Generates the key pair
        return keyPairGenerator.genKeyPair();
    }

    public static KeyPair gen_key_rsakeyspec(int keylen, String mode, String padding, String provider) throws Exception {
        RSAKeyGenParameterSpec spec = new RSAKeyGenParameterSpec(keylen, RSAKeyGenParameterSpec.F4);
        String algoDefinition = (mode.equals("") || padding.equals("")) ? "RSA" : String.format("RSA/%s/%s", mode, padding);
        KeyPairGenerator kpg = KeyPairGenerator.getInstance(algoDefinition, provider);
        kpg.initialize(spec);
        return kpg.generateKeyPair();
    }

    public static KeyPair gen_key_EC(int keylen){
        KeyPairGenerator keyGen = null;
        try {
            keyGen = KeyPairGenerator.getInstance("EC");
            //SecureRandom random = SecureRandom.getInstance("SHA1PRNG");
            //keyGen.initialize(256, random);
            keyGen.initialize(keylen);
            //KeyFactory kaif = KeyFactory.getInstance("EC");
            return keyGen.generateKeyPair();
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
       return null;
    }

    public static KeyPair gen_key_ECDSA(int keylen){
        KeyPairGenerator keyGen = null;
        try {
            keyGen = KeyPairGenerator.getInstance("ECDSA");
            //SecureRandom random = SecureRandom.getInstance("SHA1PRNG");
            //keyGen.initialize(256, random);
            keyGen.initialize(keylen);
            //KeyFactory kaif = KeyFactory.getInstance("EC");
            return keyGen.generateKeyPair();
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static KeyPair gen_dsa_key(int keyLen) throws Exception {
        KeyPairGenerator keyGen = KeyPairGenerator.getInstance("DSA");
        keyGen.initialize(keyLen);
        return keyGen.genKeyPair();
    }



}
