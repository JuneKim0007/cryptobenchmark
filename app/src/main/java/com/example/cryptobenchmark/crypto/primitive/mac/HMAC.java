package com.example.cryptobenchmark.crypto.primitive.mac;

import com.example.cryptobenchmark.misc.CryptoPrimitive;
import com.example.cryptobenchmark.misc.CryptoProvider;
import com.example.cryptobenchmark.misc.DeviceCryptoPrimitives;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import static com.example.cryptobenchmark.misc.Utils.byteArrayToString;

public class HMAC {

    Map<String, Set<String>> mac_providers = new HashMap<>();
    private static Set<String> assymmetric_primitives = new HashSet<>(
            Arrays.asList("HMAC")
    );

    public HMAC(DeviceCryptoPrimitives dcp){
        for (CryptoProvider cp : dcp.getDeviceProviders().values()){
            for (String algoId : assymmetric_primitives){
                List<String> matchingPrimitives =  cp.getProviderPrimitives().values().stream().filter(x -> x.getSimpleName().toLowerCase().matches((algoId+".*").toLowerCase())).map(CryptoPrimitive::getPrimitiveName).collect(Collectors.toList());
                for (String s : matchingPrimitives){
                    addPrimitive(s, cp.getProviderName());
                }
            }
        }
    }

    public void addPrimitive(String primitiveName, String primitiveProvider){
        if(this.mac_providers.containsKey(primitiveName)){
            this.mac_providers.get(primitiveName).add(primitiveProvider);
        }
        else{
            this.mac_providers.put(primitiveName, new HashSet<>(Collections.singletonList(primitiveProvider)));
        }
    }

    public List<String> mac_all(String message, String secret){
        List<String> macs = new ArrayList<>();
        for (String algo : this.mac_providers.keySet()){
            for (String provider : this.mac_providers.get(algo)){
                try {
                    macs.add(mac(message, secret, algo, provider));
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }
        return macs;
    }

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
