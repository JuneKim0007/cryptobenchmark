package com.example.cryptobenchmark.crypto.primitive.signature;

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
