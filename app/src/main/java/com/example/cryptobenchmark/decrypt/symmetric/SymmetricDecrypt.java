package com.example.cryptobenchmark.decrypt.symmetric;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.security.InvalidAlgorithmParameterException;
import java.security.InvalidKeyException;
import java.security.Key;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;

import static com.example.cryptobenchmark.misc.Utils.StringToByteArray;
import static com.example.cryptobenchmark.misc.Utils.StringToByteArrayBase64;

import static com.example.cryptobenchmark.misc.Utils.byteArrayToString;
import static com.example.cryptobenchmark.misc.Utils.getMethod;


public class SymmetricDecrypt {

    Map<String, Set<String>> decrypt_providers = new HashMap<>();
    Map<String, Set<String>> alg_param = new HashMap<>();

    public SymmetricDecrypt() {
        Set<String> basicTuple = new HashSet<>(
                Arrays.asList(
                        "BC",
                        "AndroidOpenSSL",
                        "AndroidKeyStoreBCWorkaround",
                        "AndroidKeyStore",
                        "Empty"
                ));
        // AES no padding
        //this.decrypt_providers.put( "AES/CBC/NoPadding", new HashSet<>(Arrays.asList("AndroidKeyStoreBCWorkaround", "AndroidOpenSSL")));
        this.decrypt_providers.put( "AES/CTR/NoPadding", new HashSet<>(Arrays.asList("AndroidKeyStoreBCWorkaround", "AndroidOpenSSL")));
        //this.decrypt_providers.put( "AES/ECB/NoPadding", new HashSet<>(Arrays.asList("AndroidKeyStoreBCWorkaround", "AndroidOpenSSL")));
        this.decrypt_providers.put( "AES/GCM/NoPadding", new HashSet<>(Arrays.asList("AndroidKeyStoreBCWorkaround", "AndroidOpenSSL")));
        /*
        // AES PKCS5Padding
         */
        this.decrypt_providers.put( "AES/CBC/PKCS5Padding", new HashSet<>(Arrays.asList("AndroidOpenSSL")));
        this.decrypt_providers.put( "AES/ECB/PKCS5Padding", new HashSet<>(Arrays.asList("AndroidOpenSSL")));
        // AES PKCS7Padding
        this.decrypt_providers.put( "AES/CBC/PKCS7Padding", new HashSet<>(Arrays.asList("AndroidKeyStoreBCWorkaround")));
        //this.decrypt_providers.put( "AES/ECB/PKCS7Padding", new HashSet<>(Arrays.asList("AndroidKeyStoreBCWorkaround")));
    }

    public List<String> get_supported_algorithm_modes(String algo){
        return this.decrypt_providers.keySet().stream()
                .filter(x -> x.startsWith(algo))
                .map(z-> z.split("/")[1])
                .collect(Collectors.toList());
    }

    public List<String> get_supported_algorithm_padds(String algo, String mode){
        return this.decrypt_providers.keySet().stream()
                .filter(x -> x.startsWith(String.format("%s/%s", algo, mode)))
                .map(z-> z.split("/")[2])
                .collect(Collectors.toList());
    }

    public Set<String> get_providers_supporting_combo(String algo, String mode, String paddingmode){
        return this.decrypt_providers.get(String.format("%s/%s/%s", algo, mode, paddingmode));
    }

    public List<String> decrypt_all(String msg, String algorithm, SecretKey privateKey, IvParameterSpec iv){
        if( this.get_supported_algorithm_modes(algorithm).isEmpty()){
            return null;
        }
        List<String> x = new ArrayList<>();
        for(String cyphermode : this.get_supported_algorithm_modes(algorithm)){
            for(String pd : this.get_supported_algorithm_padds(algorithm, cyphermode)){
                for(String provd : this.get_providers_supporting_combo(algorithm, cyphermode, pd)){
                    Method method = getMethod(this.getClass().getName(),
                            String.format("decrypt_%s", algorithm),
                            new Class[]{ String.class, String.class, String.class, SecretKey.class, String.class, IvParameterSpec.class});
                    try {
                        // x.add(encrypt_AES(msg, cyphermode, pd, privateKey, provd));
                        x.add((String) method.invoke(this, new Object[]{msg, cyphermode, pd, privateKey, provd, iv}));
                    } catch (IllegalAccessException | InvocationTargetException e) {
                        e.printStackTrace();
                    }
                }
            }
        }
        return x;
    }

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
