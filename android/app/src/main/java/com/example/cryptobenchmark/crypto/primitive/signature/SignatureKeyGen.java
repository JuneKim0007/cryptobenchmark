package com.example.cryptobenchmark.crypto.primitive.signature;

import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.NoSuchAlgorithmException;

/** Key pairs for signature algorithms. Moved out of the asymmetric cipher package. */
public class SignatureKeyGen {

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
