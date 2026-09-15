package com.example.cryptobenchmark.crypto.primitive.cipher.symmetric;

import java.security.InvalidAlgorithmParameterException;
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
import static com.example.cryptobenchmark.crypto.codec.Codec.byteArrayToStringBase64;

public class SymmetricEncrypt {

    public static int IV_SIZE = 16;

    /*
*/

    public static Map.Entry<String, IvParameterSpec> encrypt_AES(String message, String mode, String padding, Key key, String provider) {
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            String transformation = mode.equals("") || padding.equals("") ? "AES" : String.format("AES/%s/%s", mode, padding);
            cipher = provider.equals("")? Cipher.getInstance(transformation) : Cipher.getInstance(transformation, provider);
            //String algo = cipher.getAlgorithm();
            //String name = cipher.getProvider().getName();
            //AlgorithmParameters pm = cipher.getParameters();
            if (!mode.equals("ECB")){
                cipher.init(Cipher.ENCRYPT_MODE, key,  new IvParameterSpec(new byte[IV_SIZE]));
            }
            else {
                cipher.init(Cipher.ENCRYPT_MODE, key);
            }
            ciphertext = cipher.doFinal(message.getBytes());
        } catch (NoSuchProviderException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | BadPaddingException | InvalidAlgorithmParameterException e) {
            e.printStackTrace();
            return null;
        }
        return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(ciphertext), cipher.getIV() != null ? new IvParameterSpec(cipher.getIV()) :  new IvParameterSpec(new byte[]{}));
    }

    /*
     *  DES
     *   requires key of 8 bytes (64 bits)
     * */
    public static Map.Entry<String, IvParameterSpec> encrypt_DES(String message, String mode, String padding, Key key, String provider) {
        if (provider.equals("Empty")) {
            return new AbstractMap.SimpleEntry<>(message, new IvParameterSpec(new byte[]{}));
        }
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            String transformation = mode.equals("") || padding.equals("") ? "DES" : String.format("DES/%s/%s", mode, padding);
            cipher = Cipher.getInstance(transformation, provider);
            if (!mode.equals("ECB")) {
                byte[] iv = new byte[IV_SIZE];
                IvParameterSpec ips = new IvParameterSpec(iv);
                //desCipher.init(Cipher.ENCRYPT_MODE, key, ips);
                cipher.init(Cipher.ENCRYPT_MODE, key, ips);
                ciphertext = cipher.doFinal(message.getBytes());
                return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(ciphertext), new IvParameterSpec(cipher.getIV()));
            } else {
                cipher.init(Cipher.ENCRYPT_MODE, key);
                ciphertext = cipher.doFinal(message.getBytes());
                return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(ciphertext), new IvParameterSpec(new byte[]{}));
            }

        } catch (NoSuchProviderException | InvalidAlgorithmParameterException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
            return null;
        }
    }

    /*
     *  3DES
     *   requires key of 8 bytes (64 bits)
     * */
    public static Map.Entry<String, IvParameterSpec> encrypt_3DES(String message, String mode, String padding, Key key, String provider) {
        if (provider.equals("Empty")) {
            return new AbstractMap.SimpleEntry<>(message, new IvParameterSpec(new byte[]{}));
        }
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            cipher = Cipher.getInstance(String.format("DESEDE/%s/%s", mode, padding), provider);
            if (!mode.equals("ECB")) {
                IvParameterSpec ips = new IvParameterSpec(new byte[IV_SIZE]);
                cipher.init(Cipher.ENCRYPT_MODE, key, ips);
                ciphertext = cipher.doFinal(message.getBytes());
                return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(ciphertext), new IvParameterSpec(cipher.getIV()));
            } else {
                cipher.init(Cipher.ENCRYPT_MODE, key);
                ciphertext = cipher.doFinal(message.getBytes());
                return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(ciphertext), new IvParameterSpec(new byte[]{}));
            }

        } catch (NoSuchProviderException | InvalidAlgorithmParameterException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
            return null;
        }
    }

    /*
     *  Blowfish
     *   requires key of 8 bytes (64 bits)
     * */
    public static Map.Entry<String, IvParameterSpec> encrypt_BLOWFISH(String message, String mode, String padding, Key key, String provider) {
        if (provider.equals("Empty")) {
            return new AbstractMap.SimpleEntry<>(message, new IvParameterSpec(new byte[]{}));
        }
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            cipher = Cipher.getInstance("BLOWFISH", provider);
            cipher.init(Cipher.ENCRYPT_MODE, key);
            ciphertext = cipher.doFinal(message.getBytes());
            return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(ciphertext), new IvParameterSpec(new byte[]{}));

        } catch (NoSuchProviderException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
            return null;
        }
    }

    public static Map.Entry<String, IvParameterSpec> encrypt_ARC4(String message, String mode, String padding, Key key, String provider) {
        if (provider.equals("Empty")) {
            return new AbstractMap.SimpleEntry<>(message, new IvParameterSpec(new byte[]{}));
        }
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            cipher = Cipher.getInstance("ARC4", provider);
            cipher.init(Cipher.ENCRYPT_MODE, key);
            ciphertext = cipher.doFinal(message.getBytes());
            return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(ciphertext), new IvParameterSpec(new byte[]{}));

        } catch (NoSuchProviderException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
            return null;
        }
    }

    // ChaCha20-Poly1305 is almost 3 times faster than AES when the CPU does not provide dedicated AES instructions. Intel processors provide AES-NI instruction set [1]
    // ChaCha20 is not vulnerable to cache-collision timing attacks unlike AES [1]
    public static Map.Entry<String, IvParameterSpec> encrypt_ChaCha20(String msg, String mode,
                                                                      String padding,
                                                                      Key key,
                                                                      String provider){
        int NONCE_LEN = 12;
        byte[] nonce = new byte[12]; // getNonce(); avoid
        IvParameterSpec ivParameterSpec = new IvParameterSpec(nonce);
        try{
            Cipher cipher = Cipher.getInstance("ChaCha20");
            cipher.init(Cipher.ENCRYPT_MODE, key, ivParameterSpec);
            byte[] messageCipher = cipher.doFinal(msg.getBytes());
            // Prepend the nonce with the message cipher
            byte[] cipherText = new byte[messageCipher.length + NONCE_LEN];
            System.arraycopy(nonce, 0, cipherText, 0, NONCE_LEN);
            System.arraycopy(messageCipher, 0, cipherText, NONCE_LEN,
                    messageCipher.length);
            return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(cipherText), ivParameterSpec);
        }catch (Exception e){
            e.printStackTrace();
        }
        return null;

    }
}