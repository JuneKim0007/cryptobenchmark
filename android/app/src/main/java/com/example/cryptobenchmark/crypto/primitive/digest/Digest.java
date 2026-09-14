package com.example.cryptobenchmark.crypto.primitive.digest;

import com.hunter.library.debug.HunterDebug;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import static com.example.cryptobenchmark.crypto.codec.Codec.StringToByteArray;
import static com.example.cryptobenchmark.crypto.codec.Codec.byteArrayToString;
import static com.example.cryptobenchmark.misc.Utils.getMethod;

public class Digest {

    Map<String, Set<String>> digestsProviders = new HashMap<>();
    private static Set<String> digestAlgorithms = new HashSet<>(Arrays.asList(
            "MD5", "SHA1", "SHA224", "SHA226", "SHA256", "SHA384", "SHA512",
            "MD-5", "SHA-1", "SHA-224", "SHA-226", "SHA-256", "SHA-384", "SHA-512"
    ));
    private static Set<String> excludedProviders = new HashSet<>(Arrays.asList("BC"));

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

    public static String digest_MD5_Empty(String message){
        return message;
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
