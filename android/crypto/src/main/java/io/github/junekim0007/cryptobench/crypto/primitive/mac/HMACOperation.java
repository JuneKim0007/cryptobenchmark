package io.github.junekim0007.cryptobench.crypto.primitive.mac;

@FunctionalInterface
public interface HMACOperation {

    String do_hmac(String message, String key, String provider);
}
