package io.github.junekim0007.cryptobench.crypto.primitive.cipher.asymmetric;

import java.security.InvalidKeyException;
import java.security.Key;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;

import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.crypto.spec.IvParameterSpec;

import static io.github.junekim0007.cryptobench.crypto.codec.Codec.StringToByteArrayBase64;

import static io.github.junekim0007.cryptobench.crypto.codec.Codec.byteArrayToString;

public class AssymmetricDecrypt {

    public static String decrypt_RSA(String message, String mode, String padding, Key key, String provider, IvParameterSpec iv){
        Cipher cipher = null;
        try {
            cipher = Cipher.getInstance(String.format("RSA/%s/%s", mode, padding), provider);
            cipher.init(Cipher.DECRYPT_MODE, key);
            byte[] plainText = cipher.doFinal(StringToByteArrayBase64(message));
            return byteArrayToString(plainText);
        } catch (NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | NoSuchProviderException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String decrypt_RSA(String message, Key key, String provider, IvParameterSpec iv){
        Cipher cipher = null;
        try {
            cipher = Cipher.getInstance("RSA", provider);
            cipher.init(Cipher.DECRYPT_MODE, key);
            byte[] plainText = cipher.doFinal(StringToByteArrayBase64(message));
            return byteArrayToString(plainText);
        } catch (NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | NoSuchProviderException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
        }
        return null;
    }

}
