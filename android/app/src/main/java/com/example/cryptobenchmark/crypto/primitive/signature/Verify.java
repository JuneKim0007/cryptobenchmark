package com.example.cryptobenchmark.crypto.primitive.signature;

import com.example.cryptobenchmark.environment.discovery.CryptoPrimitive;
import com.example.cryptobenchmark.environment.discovery.CryptoProvider;
import com.example.cryptobenchmark.environment.discovery.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.benchmark.preparation.registry.PrimitiveStore;

import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.security.PublicKey;
import java.security.Signature;
import java.security.SignatureException;
import java.util.List;
import java.util.stream.Collectors;

import static com.example.cryptobenchmark.crypto.codec.Codec.StringToByteArray;
import static com.example.cryptobenchmark.crypto.codec.Codec.StringToByteArrayBase64;


public class Verify extends PrimitiveStore {

    public Verify() {
        super();
    }

    public Verify(DeviceCryptoPrimitives dcp){
        this();
        for (CryptoProvider cp : dcp.getDeviceProviders().values()){
            for (String algoId : primitives){
                List<String> matchingPrimitives =  cp.getProviderPrimitives().values().stream().filter(x -> x.getSimpleName().matches(""+algoId+".*")).map(CryptoPrimitive::getPrimitiveName).collect(Collectors.toList());
                for (String s : matchingPrimitives){
                    addProviderForPrimitive(s, cp.getProviderName());
                }
            }
        }
    }



    public Verify(DeviceCryptoPrimitives dcp, List<String> primitives){
        this();
        for (CryptoProvider cp : dcp.getDeviceProviders().values()){
            for (String algoId : primitives){
                //List<String> matchingPrimitives =  cp.getProviderPrimitives().values().stream().filter(x -> x.getSimpleName().matches(""+algoId+".*")).map(CryptoPrimitive::getPrimitiveName).collect(Collectors.toList());
                List<String> matchingPrimitives =  cp.getProviderPrimitives().values().stream().filter(x -> x.getPrimitiveName().toLowerCase().equals(algoId.toLowerCase())).map(CryptoPrimitive::getPrimitiveName).collect(Collectors.toList());
                for (String s : matchingPrimitives){
                    addProviderForPrimitive(s, cp.getProviderName());
                }
            }
        }
        addPrimitives(primitives);
    }

    public static boolean verify(String message, String signature, String algo, PublicKey key){
        Signature s = null;
        try {
            s = Signature.getInstance(algo);
            s.initVerify(key);
            s.update(message.getBytes());
            return s.verify(StringToByteArrayBase64(signature));
        } catch (NoSuchAlgorithmException | InvalidKeyException | SignatureException e) {
            e.printStackTrace();
        }
        return false;
    }

    public static boolean verify(String message, String signature, String algo, PublicKey key, String provider){
        Signature s = null;
        try {
            s = Signature.getInstance(algo, provider);
            s.initVerify(key);
            s.update(message.getBytes());
            return s.verify(StringToByteArrayBase64(signature));
        } catch (NoSuchAlgorithmException | InvalidKeyException | SignatureException | NoSuchProviderException e) {
            e.printStackTrace();
        }
        return false;
    }

    public static boolean verify_b(byte[] message, byte[] signature, String algo, PublicKey key){
        Signature s = null;
        try {
            s = Signature.getInstance(algo);
            s.initVerify(key);
            s.update(message);
            return s.verify(signature);
        } catch (NoSuchAlgorithmException | InvalidKeyException | SignatureException e) {
            e.printStackTrace();
        }
        return false;
    }
}
