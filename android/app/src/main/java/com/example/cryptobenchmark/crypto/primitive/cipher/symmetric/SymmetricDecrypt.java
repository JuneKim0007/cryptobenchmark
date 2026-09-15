package com.example.cryptobenchmark.crypto.primitive.cipher.symmetric;

import java.security.InvalidAlgorithmParameterException;
import java.security.InvalidKeyException;
import java.security.Key;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;

import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.crypto.spec.IvParameterSpec;

import static com.example.cryptobenchmark.crypto.codec.Codec.StringToByteArrayBase64;

import static com.example.cryptobenchmark.crypto.codec.Codec.byteArrayToString;

public class SymmetricDecrypt {

    public static String decrypt_AES(String message, String mode, String padding, Key key, String provider, IvParameterSpec iv){
        Cipher cipher = null;
        try {
            cipher = Cipher.getInstance(String.format("AES/%s/%s", mode, padding), provider);
            if(!mode.equals("ECB")){
                cipher.init(Cipher.DECRYPT_MODE, key, iv);
            }
            else{
                cipher.init(Cipher.DECRYPT_MODE, key);
            }
            byte[] plainText = cipher.doFinal(StringToByteArrayBase64(message));
            return byteArrayToString(plainText); //new String(plainText);
        } catch (NoSuchAlgorithmException | NoSuchPaddingException | InvalidAlgorithmParameterException | InvalidKeyException | NoSuchProviderException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String decrypt_BLOWFISH(String message, String mode, String padding, Key key, String provider, IvParameterSpec iv){
        Cipher cipher = null;
        try {
            cipher = Cipher.getInstance("BLOWFISH", provider);
            cipher.init(Cipher.DECRYPT_MODE, key, iv);
            byte[] plainText = cipher.doFinal(StringToByteArrayBase64(message));
            return byteArrayToString(plainText);
        } catch (NoSuchAlgorithmException | NoSuchPaddingException | InvalidAlgorithmParameterException | InvalidKeyException | NoSuchProviderException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
        }
        return null;
    }
    public static String decrypt_ARC4(String message, String mode, String padding, Key key, String provider, IvParameterSpec iv){
        Cipher cipher = null;
        try {
            cipher = Cipher.getInstance("ARC4", provider);
            cipher.init(Cipher.DECRYPT_MODE, key);
            //cipher.init(Cipher.DECRYPT_MODE, key, iv);
            byte[] plainText = cipher.doFinal(StringToByteArrayBase64(message));
            return byteArrayToString(plainText);
        } catch (NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | NoSuchProviderException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String decrypt_3DES(String message, String mode, String padding, Key key, String provider, IvParameterSpec iv){
        Cipher cipher = null;
        try {
            cipher = Cipher.getInstance(String.format("DESEDE/%s/%s", mode, padding), provider);
            if(mode.equals("CBC")){
                cipher.init(Cipher.DECRYPT_MODE, key, iv);
            }
            else{
                cipher.init(Cipher.DECRYPT_MODE, key);
            }
            //
            byte[] plainText = cipher.doFinal(StringToByteArrayBase64(message));
            return byteArrayToString(plainText);
        } catch (NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | NoSuchProviderException | IllegalBlockSizeException | BadPaddingException | InvalidAlgorithmParameterException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String decrypt_DES(String message, String mode, String padding, Key key, String provider, IvParameterSpec iv){
        Cipher cipher = null;
        try {
            cipher = Cipher.getInstance(String.format("DES/%s/%s", mode, padding), provider);
            cipher.init(Cipher.DECRYPT_MODE, key);
            //cipher.init(Cipher.DECRYPT_MODE, key, iv);
            byte[] plainText = cipher.doFinal(StringToByteArrayBase64(message));
            return byteArrayToString(plainText);
        } catch (NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | NoSuchProviderException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String decrypt_ChaCha20(String msg, String mode, String padding, Key key, String provider, IvParameterSpec iv){
        int NONCE_LEN = 12;
        byte[] nonce = new byte[NONCE_LEN];
        byte[] input = StringToByteArrayBase64(msg);
        System.arraycopy(input, 0, nonce, 0, NONCE_LEN);
        byte[] messageCipher = new byte[input.length - NONCE_LEN];
        System.arraycopy(input, NONCE_LEN, messageCipher, 0, input.length - NONCE_LEN);
        IvParameterSpec ivParameterSpec = new IvParameterSpec(nonce);

        try {
            Cipher cipher = Cipher.getInstance("ChaCha20");
            cipher.init(Cipher.DECRYPT_MODE, key, ivParameterSpec);
            return byteArrayToString(cipher.doFinal(messageCipher));
        } catch (InvalidKeyException | InvalidAlgorithmParameterException | IllegalBlockSizeException | BadPaddingException | NoSuchAlgorithmException | NoSuchPaddingException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static String decrypt_ChaCha20Poly(String msg,  String mode, String padding, Key key, String provider, IvParameterSpec iv){
        int NONCE_LEN = 12;
        byte[] nonce = new byte[NONCE_LEN];
        byte[] input = StringToByteArrayBase64(msg);
        System.arraycopy(input, 0, nonce, 0, NONCE_LEN);
        byte[] messageCipher = new byte[input.length - NONCE_LEN];
        System.arraycopy(input, NONCE_LEN, messageCipher, 0, input.length - NONCE_LEN);
        IvParameterSpec ivParameterSpec = new IvParameterSpec(nonce);

        try {
            Cipher cipher = Cipher.getInstance("ChaCha20/Poly1305/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, key, ivParameterSpec);
            return new String(cipher.doFinal(messageCipher));
        } catch (InvalidKeyException | InvalidAlgorithmParameterException | IllegalBlockSizeException | BadPaddingException | NoSuchAlgorithmException | NoSuchPaddingException e) {
            e.printStackTrace();
        }
        return null;
    }
}
