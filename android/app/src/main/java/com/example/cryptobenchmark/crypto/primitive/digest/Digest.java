package com.example.cryptobenchmark.crypto.primitive.digest;


import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;

import static com.example.cryptobenchmark.crypto.codec.Codec.StringToByteArray;
import static com.example.cryptobenchmark.crypto.codec.Codec.byteArrayToString;

public class Digest {

    public static String digest(String message, String algo, String provider){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance(algo, provider);
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());

        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
        }
        return "";
    }

    public static String digest_MD5(String message, String provider){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("MD5", provider);
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
        }
        return "";
    }

    public static String digest_MD5(String message){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("MD5");
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());

        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return "";
    }

    /*
     *  -------------------- SHA1 --------------------
     * */
    public static String digest_SHA1(String message, String provider){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("SHA-1", provider);
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
        }
        return "";
    }

    /*
     *  -------------------- SHA224 --------------------
     * */
    public static String digest_SHA224(String message, String provider){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("SHA-224", provider);
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
        }
        return "";
    }

    /*
     *  -------------------- SHA256 --------------------
     * */
    public static String digest_SHA256(String message, String provider){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("SHA-256", provider);
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
        }
        return "";
    }

    /*
     *  -------------------- SHA384 --------------------
     * */
    public static String digest_SHA384(String message, String provider){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("SHA-384", provider);
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
        }
        return "";
    }

    /*
     *  -------------------- SHA512 --------------------
     * */
    public static String digest_SHA512(String message, String provider){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("SHA-512", provider);
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
        }
        return "";
    }

    /*
     *  -------------------- SHA1 --------------------
     * */
    public static String digest_SHA1(String message){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("SHA-1");
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return "";
    }

    /*
     *  -------------------- SHA224 --------------------
     * */
    public static String digest_SHA224(String message){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("SHA-224");
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return "";
    }

    /*
     *  -------------------- SHA256 --------------------
     * */
    public static String digest_SHA256(String message){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("SHA-256");
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return "";
    }

    /*
     *  -------------------- SHA384 --------------------
     * */
    public static String digest_SHA384(String message){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("SHA-384");
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return "";
    }

    /*
     *  -------------------- SHA512 --------------------
     * */
    public static String digest_SHA512(String message){
        try {
            MessageDigest digest = java.security.MessageDigest
                    .getInstance("SHA-512");
            digest.update(StringToByteArray(message));
            return byteArrayToString(digest.digest());
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return "";
    }
}
