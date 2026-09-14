package com.example.cryptobenchmark.crypto.primitive.digest;

import com.example.cryptobenchmark.misc.CryptoPrimitive;
import com.example.cryptobenchmark.misc.CryptoProvider;
import com.example.cryptobenchmark.misc.DeviceCryptoPrimitives;
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

import static com.example.cryptobenchmark.misc.Utils.StringToByteArray;
import static com.example.cryptobenchmark.misc.Utils.byteArrayToString;
import static com.example.cryptobenchmark.misc.Utils.getMethod;

public class Digest {

    Map<String, Set<String>> digestsProviders = new HashMap<>();
    private static Set<String> digestAlgorithms = new HashSet<>(Arrays.asList(
            "MD5", "SHA1", "SHA224", "SHA226", "SHA256", "SHA384", "SHA512",
            "MD-5", "SHA-1", "SHA-224", "SHA-226", "SHA-256", "SHA-384", "SHA-512"
    ));
    private static Set<String> excludedProviders = new HashSet<>(Arrays.asList("BC"));


    public Digest(DeviceCryptoPrimitives dcp){
        for (CryptoProvider cp : dcp.getDeviceProviders().values()){
            for (String algoId : digestAlgorithms){
                List<String> matchingPrimitives =  cp.getProviderPrimitives().values().stream().filter(x -> x.getPrimitiveName().equals(algoId)).map(CryptoPrimitive::getPrimitiveName).collect(Collectors.toList());
                for (String s : matchingPrimitives){
                    addPrimitive(s, cp.getProviderName());
                }
            }
        }
    }

    public void addPrimitive(String primitiveName, String primitiveProvider){
        if (excludedProviders.contains(primitiveProvider)){
            return;
        }
        if(this.digestsProviders.containsKey(primitiveName)){
            this.digestsProviders.get(primitiveName).add(primitiveProvider);
        }
        else{
            this.digestsProviders.put(primitiveName, new HashSet<>(Collections.singletonList(primitiveProvider)));
        }
    }

    /*
    public Digest(){
        List<String> basicTriple = new ArrayList<>(
                Arrays.asList(
                        "BC",
                        "AndroidOpenSSL",
                        "Empty"
                ));

        this.digests_providers.put( "MD5", basicTriple);
        this.digests_providers.put( "SHA1", basicTriple);
        this.digests_providers.put( "SHA224", basicTriple);
        this.digests_providers.put( "SHA226", basicTriple);
        this.digests_providers.put( "SHA256", basicTriple);
        this.digests_providers.put( "SHA384", basicTriple);
        this.digests_providers.put( "SHA512", basicTriple);
    }*/

    public List<String> digest_all(String msg){
        List<String> x = new ArrayList<>();
        for(String algorithm : this.digestsProviders.keySet()){
            for(String provider : this.digestsProviders.get(algorithm)){
                x.add(digest(msg, algorithm, provider));
            }
        }
        return x;
    }


    public List<String> digest_all(String msg, String algorithm){
        if( ! this.digestsProviders.containsKey(algorithm) ){
            return null;
        }
        Set<String> algo_providers = this.digestsProviders.get(algorithm);
        List<String> x = new ArrayList<>();
        for(String provider : algo_providers){
            x.add(digest(msg, algorithm, provider));
            /*Method method = getMethod(this.getClass().getName(), String.format("digest_%s", algorithm),  new Class[]{ String.class, String.class});
            try {
                x.add((String) method.invoke(this, new Object[]{msg, provider}));
            } catch (IllegalAccessException | InvocationTargetException e) {
                e.printStackTrace();
            }*/
        }
        return x;
    }

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
