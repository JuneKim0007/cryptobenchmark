package com.example.cryptobenchmark.crypto.primitive.cipher.symmetric;

import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import javax.crypto.spec.SecretKeySpec;
import java.security.InvalidAlgorithmParameterException;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;

public class SymmetricKeyGen {
    Map<String, Set<String>> keygen_providers = new HashMap<>();


    public SymmetricKeyGen(){
        this.keygen_providers.put( "AES", new HashSet<>(Arrays.asList(
                "AndroidOpenSSL", "AndroidKeyStore", "Empty")));
    }

    public static IvParameterSpec generateIv() {
        byte[] iv = new byte[16];
        new SecureRandom().nextBytes(iv);
        return new IvParameterSpec(iv);
    }



    public static SecretKey gen_key_AES_AndroidKeyStore(int keysize){
        KeyGenerator keyGenerator = null;
        try {
            keyGenerator = KeyGenerator.getInstance(
                    KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        try {
            keyGenerator.init(new KeyGenParameterSpec.Builder("benchmark",
                    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setKeySize(keysize)
                    .setBlockModes(KeyProperties.BLOCK_MODE_CBC)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_PKCS7)
                    .build());
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
            return null;
        }

        return keyGenerator.generateKey();
    }

    public static SecretKey gen_key_AES_AndroidKeyStore(int keysize, String mode, String padding){
        KeyGenerator keyGenerator = null;
        try {
            keyGenerator = KeyGenerator.getInstance(
                    KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        try {
            keyGenerator.init(new KeyGenParameterSpec.Builder("benchmark",
                    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setKeySize(keysize)
                    .setBlockModes(mode)
                    .setEncryptionPaddings(padding)
                    .setRandomizedEncryptionRequired(false)
                    .build());
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
            return null;
        }

        return keyGenerator.generateKey();
    }

    public static SecretKey gen_key_AES_AndroidKeyStoreBCWorkaround(int keysize, String mode, String padding){
        KeyGenerator keyGenerator = null;
        try {
            keyGenerator = KeyGenerator.getInstance(
                    KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        try {
            keyGenerator.init(new KeyGenParameterSpec.Builder("benchmark",
                    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setKeySize(keysize)
                    .setBlockModes(mode)
                    .setEncryptionPaddings(padding)
                    .build());
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
            return null;
        }

        return keyGenerator.generateKey();
    }

    public static SecretKey gen_key_DES(int keysize, String mode, String padding, String provider){
        // keys size: 56 bits
        // block size: 64 bits
        KeyGenerator keygenerator = null;
        try {
            keygenerator = KeyGenerator.getInstance(String.format("DES/%s/%s", mode, padding), provider);
            //keygenerator = KeyGenerator.getInstance("DES", "BC");
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        keygenerator.init(keysize);
        return  keygenerator.generateKey();
    }

    public static SecretKey gen_key_DES_AndroidKeyStoreBCWorkaround(int keysize, String mode, String padding){
        // keys size: 56 bits
        // block size: 64 bits
        KeyGenerator keygenerator = null;
        try {
            //keygenerator = KeyGenerator.getInstance(String.format("DES/%s/%s", mode, padding), "BC");
            keygenerator = KeyGenerator.getInstance("DES", "AndroidKeyStoreBCWorkaround");
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        keygenerator.init(keysize);
        return  keygenerator.generateKey();
    }



    public static SecretKey gen_key_3DES_AndroidKeyStore(int keysize, String mode, String padding){
        // keys size: 56 bits
        // block size: 64 bits
        KeyGenerator keygenerator = null;
        try {
            //keygenerator = KeyGenerator.getInstance(String.format("DES/%s/%s", mode, padding), "BC");
            keygenerator = KeyGenerator.getInstance("DESEDE", "AndroidKeyStore");
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        try {
            keygenerator.init(new KeyGenParameterSpec.Builder("benchmark",
                    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setBlockModes(mode)
                    .setEncryptionPaddings(padding)
                    .setRandomizedEncryptionRequired(false)
                    .build());
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
            return null;
        }
        keygenerator.init(keysize);
        return  keygenerator.generateKey();
    }

    public static SecretKey gen_key_3DES_AndroidKeyStoreBCWorkaround(int keysize, String mode, String padding){
        // keys size: 56 bits
        // block size: 64 bits
        KeyGenerator keygenerator = null;
        try {
            keygenerator = KeyGenerator.getInstance(String.format("DESEDE/%s/%s", mode, padding), "BC");
            //keygenerator = KeyGenerator.getInstance("DESEDE", "AndroidKeyStoreBCWorkaround");
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        try {
            keygenerator.init(new KeyGenParameterSpec.Builder("benchmark",
                    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setBlockModes(KeyProperties.BLOCK_MODE_CBC)
                    .setEncryptionPaddings(padding)
                    .build());
        } catch (InvalidAlgorithmParameterException e) {
            e.printStackTrace();
            return null;
        }
        keygenerator.init(keysize);
        return  keygenerator.generateKey();
    }

    public static SecretKey gen_key_3DES_AndroidOpenSSL(int keysize, String mode, String padding){
        // keys size: 56 bits
        // block size: 64 bits
        KeyGenerator keygenerator = null;
        try {
            //keygenerator = KeyGenerator.getInstance(String.format("DES/%s/%s", mode, padding), "BC");
            keygenerator = KeyGenerator.getInstance("DESEDE", "AndroidOpenSSL");
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        keygenerator.init(keysize);
        return  keygenerator.generateKey();
    }

    public static SecretKey gen_key_BLOWFISH(int keysize,
                                                String provider){
        KeyGenerator keygenerator = null;
        try {
            keygenerator = KeyGenerator.getInstance("BLOWFISH", provider);
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        keygenerator.init(keysize);
        return  keygenerator.generateKey();
    }

    public static SecretKey gen_key_ARC4(int keysize, String provider){
        KeyGenerator keygenerator = null;
        try {
            keygenerator = KeyGenerator.getInstance("ARC4", provider);
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        keygenerator.init(keysize);
        return  keygenerator.generateKey();
    }

    public static SecretKey gen_key_ARC4_AndroidOpenSSL(int keysize, String mode, String padding){
        KeyGenerator keygenerator = null;
        try {
            keygenerator = KeyGenerator.getInstance("ARC4", "AndroidOpenSSL");
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        keygenerator.init(keysize);
        return  keygenerator.generateKey();
    }

    public static SecretKey gen_key_ARC4_BC(int keysize, String mode, String padding){
        KeyGenerator keygenerator = null;
        try {
            keygenerator = KeyGenerator.getInstance("ARC4", "BC");
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        keygenerator.init(keysize);
        return  keygenerator.generateKey();
    }

    public static SecretKey gen_key_AES(int keysize, String mode, String padd, String provider){
        KeyGenerator keygen = null;
        try {
            keygen = KeyGenerator.getInstance("AES", provider);
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        keygen.init(keysize);
        return keygen.generateKey();
    }

    public static SecretKey gen_key_AES(int keysize, String mode, String padd){
        KeyGenerator keygen = null;
        try {
            keygen = KeyGenerator.getInstance("AES");
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
            return null;
        }
        keygen.init(keysize);
        return keygen.generateKey();
    }

    public static SecretKey gen_key(String algorithm, int keysize, String provider){
        KeyGenerator keygen = null;
        try {
            keygen = KeyGenerator.getInstance(algorithm, provider);
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
            return null;
        }
        keygen.init(keysize);
        return keygen.generateKey();
    }

    public static SecretKey gen_key_ChaCha20(int keysize, String provider){
        KeyGenerator keyGen = null;
        try {
            keyGen = KeyGenerator.getInstance("ChaCha20", provider);
            keyGen.init(keysize, SecureRandom.getInstanceStrong());
            SecretKey secretKey = keyGen.generateKey();
            return secretKey;
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
        }
        return null;
    }

}
