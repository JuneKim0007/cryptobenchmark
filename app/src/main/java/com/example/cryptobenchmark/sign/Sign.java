package com.example.cryptobenchmark.sign;

import com.example.cryptobenchmark.misc.CryptoPrimitive;
import com.example.cryptobenchmark.misc.CryptoProvider;
import com.example.cryptobenchmark.misc.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.misc.PrimitiveStore;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.security.PrivateKey;
import java.security.Signature;
import java.security.SignatureException;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import static com.example.cryptobenchmark.misc.Utils.byteArrayToString;
import static com.example.cryptobenchmark.misc.Utils.byteArrayToStringBase64;



public class Sign extends PrimitiveStore {

    public Sign() {
        super();
    }

    public Sign(DeviceCryptoPrimitives dcp){
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

    public Sign(DeviceCryptoPrimitives dcp, List<String> primitives){
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

    public static String sign(String message, String fullAlgorithmDefinition, PrivateKey key){
        try {
            Signature s = Signature.getInstance(fullAlgorithmDefinition);
            s.initSign(key);
            s.update(message.getBytes());
            return byteArrayToStringBase64(s.sign());
        } catch (InvalidKeyException | SignatureException | NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String sign(String message,String algo, PrivateKey key, String provider){
        try {
            Signature s = Signature.getInstance(algo, provider);
            s.initSign(key);
            s.update(message.getBytes());
            return byteArrayToStringBase64(s.sign());
        } catch (InvalidKeyException | SignatureException | NoSuchAlgorithmException | NoSuchProviderException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static byte[] sign_b(String message,String algo, PrivateKey key){
        try {
            Signature s = Signature.getInstance(algo);
            s.initSign(key);
            s.update(message.getBytes());
            return s.sign();
        } catch (InvalidKeyException | SignatureException | NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return null;
    }


    public List<String> sign_all(String message, PrivateKey key) {
        List<String> l = new ArrayList<>();
        for(String primitive : providers.keySet()){
            for (String provider : providers.get(primitive)){
                //System.out.println(provider);
                l.add(sign(message, primitive, key, provider));
            }
        }
        return l;
    }

}
