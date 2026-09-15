package com.example.cryptobenchmark.crypto.primitive.signature;

import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.security.PrivateKey;
import java.security.Signature;
import java.security.SignatureException;
import static com.example.cryptobenchmark.crypto.codec.Codec.byteArrayToStringBase64;

public class Sign {

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

}
