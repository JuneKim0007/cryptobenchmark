package com.example.cryptobenchmark.crypto.primitive.mac;


import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import static com.example.cryptobenchmark.crypto.codec.Codec.byteArrayToString;

public class HMAC {

    public static String mac(String message, String secret, String algo, String provider) throws Exception{
        Mac sha256_HMAC = Mac.getInstance(algo, provider);
        SecretKeySpec secretKey = new SecretKeySpec(secret.getBytes(), algo);
        sha256_HMAC.init(secretKey);
        return byteArrayToString(sha256_HMAC.doFinal(message.getBytes()));
    }

    public static String mac(String message, String secret, String algo) throws Exception{
        Mac sha256_HMAC = Mac.getInstance(algo);
        SecretKeySpec secretKey = new SecretKeySpec(secret.getBytes(), algo);
        sha256_HMAC.init(secretKey);
        return byteArrayToString(sha256_HMAC.doFinal(message.getBytes()));
    }

    public static String mac_MD5(String message, String secret){
        String algo = "HMACMD5";
        try {
            return mac(message, secret, algo);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_SHA1(String message, String secret){
        String algo = "HmacSHA1";
        try {
            return mac(message, secret, algo);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_SHA224(String message, String secret){
        String algo = "HmacSHA224";
        try {
            return mac(message, secret, algo);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_SHA256(String message, String secret){
        String algo = "HmacSHA256";
        try {
            return mac(message, secret, algo);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_SHA384(String message, String secret){
        String algo = "HmacSHA384";
        try {
            return mac(message, secret, algo);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_SHA512(String message, String secret){
        String algo = "HmacSHA512";
        try {
            return mac(message, secret, algo);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_MD5(String message, String secret, String provider){
        String algo = "HMACMD5";
        try {
            return mac(message, secret, algo, provider);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_SHA1(String message, String secret, String provider){
        String algo = "HmacSHA1";
        try {
            return mac(message, secret, algo, provider);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_SHA224(String message, String secret, String provider){
        String algo = "HmacSHA224";
        try {
            return mac(message, secret, algo, provider);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_SHA256(String message, String secret, String provider){
        String algo = "HmacSHA256";
        try {
            return mac(message, secret, algo, provider);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_SHA384(String message, String secret, String provider){
        String algo = "HmacSHA384";
        try {
            return mac(message, secret, algo, provider);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String mac_SHA512(String message, String secret, String provider){
        String algo = "HmacSHA512";
        try {
            return mac(message, secret, algo, provider);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}
