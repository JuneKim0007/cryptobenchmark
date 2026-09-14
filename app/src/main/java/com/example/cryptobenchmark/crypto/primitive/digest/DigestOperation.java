package com.example.cryptobenchmark.crypto.primitive.digest;

@FunctionalInterface
public interface DigestOperation {
    String digest(String msg, String provider);
}
