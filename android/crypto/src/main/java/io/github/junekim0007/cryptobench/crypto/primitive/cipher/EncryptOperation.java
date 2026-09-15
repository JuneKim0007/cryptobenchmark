package io.github.junekim0007.cryptobench.crypto.primitive.cipher;

import java.security.Key;
import java.util.Map;
import javax.crypto.spec.IvParameterSpec;

@FunctionalInterface
public interface EncryptOperation {
    Map.Entry<String, IvParameterSpec> encrypt(String message, String mode, String padding, Key key, String provider);
}
