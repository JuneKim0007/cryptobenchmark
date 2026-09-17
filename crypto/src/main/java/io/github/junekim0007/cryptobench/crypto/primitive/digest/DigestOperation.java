package io.github.junekim0007.cryptobench.crypto.primitive.digest;

@FunctionalInterface
public interface DigestOperation {
    String digest(String msg, String provider);
}
