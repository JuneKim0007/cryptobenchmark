package com.example.cryptobenchmark.crypto.primitive.signature;

import java.security.PublicKey;

public interface VerifyOperation {

    boolean verify(String msg, String signature, String algo, PublicKey pubkey, String provider);

}
