package com.example.cryptobenchmark.crypto.primitive.signature;

import java.security.PrivateKey;

@FunctionalInterface
public interface SignOperation {
    public String sign(String message, String algoFullDefinition, PrivateKey pk , String provider);
}
