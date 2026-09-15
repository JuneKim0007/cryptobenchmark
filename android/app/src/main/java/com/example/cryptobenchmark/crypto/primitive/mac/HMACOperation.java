package com.example.cryptobenchmark.crypto.primitive.mac;

@FunctionalInterface
public interface HMACOperation {

    String do_hmac(String message, String key, String provider);
}
