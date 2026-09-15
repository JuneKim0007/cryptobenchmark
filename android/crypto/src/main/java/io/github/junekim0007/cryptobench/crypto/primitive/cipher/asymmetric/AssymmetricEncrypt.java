package io.github.junekim0007.cryptobench.crypto.primitive.cipher.asymmetric;

import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.Key;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.util.AbstractMap;

import java.util.Map;

import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.crypto.spec.IvParameterSpec;

import static io.github.junekim0007.cryptobench.crypto.codec.Codec.byteArrayToString;
import static io.github.junekim0007.cryptobench.crypto.codec.Codec.byteArrayToStringBase64;

public class AssymmetricEncrypt {

    public static Map.Entry<String, IvParameterSpec> encrypt_RSA(String message, String mode, String padding, Key key, String provider) {
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            cipher = Cipher.getInstance(String.format("RSA/%s/%s", mode, padding), provider);
            cipher.init(Cipher.ENCRYPT_MODE, key);
            ciphertext = cipher.doFinal(message.getBytes(StandardCharsets.UTF_8));
            return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(ciphertext), new IvParameterSpec(new byte[8]));

        } catch (NoSuchProviderException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException  | BadPaddingException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static Map.Entry<String, IvParameterSpec> encrypt_RSA(String message, Key key, String provider) {
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            cipher = Cipher.getInstance("RSA", provider);
            cipher.init(Cipher.ENCRYPT_MODE, key);
            ciphertext = cipher.doFinal(message.getBytes(StandardCharsets.UTF_8));
            return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(ciphertext), new IvParameterSpec(new byte[]{}));

        } catch (NoSuchProviderException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
            return null;
        }
    }

    public static Map.Entry<String, IvParameterSpec> encryptEC(String message, Key key, String provider) {
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            cipher = Cipher.getInstance("EC", provider);
            cipher.init(Cipher.ENCRYPT_MODE, key);
            ciphertext = cipher.doFinal(message.getBytes(StandardCharsets.UTF_8));
            return new AbstractMap.SimpleEntry<>(byteArrayToString(ciphertext), new IvParameterSpec(new byte[]{}));

        } catch (NoSuchProviderException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
            return null;
        }
    }
}