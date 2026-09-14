package com.example.cryptobenchmark.crypto.primitive.cipher.symmetric;

import com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricKeyGen;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.security.AlgorithmParameters;
import java.security.InvalidAlgorithmParameterException;
import java.security.InvalidKeyException;
import java.security.Key;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.util.AbstractMap;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
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
import static com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricKeyGen.gen_key_AES;
import static com.example.cryptobenchmark.crypto.codec.Codec.byteArrayToString;
import static com.example.cryptobenchmark.crypto.codec.Codec.byteArrayToStringBase64;
import static com.example.cryptobenchmark.misc.Utils.getMethod;


public class SymmetricEncrypt {

    public static int IV_SIZE = 16;

    Map<String, Set<String>> encrypt_providers = new HashMap<>();
    private static Set<String> symmetric_primitives = new HashSet<>(
            Arrays.asList("AES", "DES", "BLOWFISH", "ARC4")
    );

    private static Set<String> excluded_symmetric_primitives = new HashSet<>(
            Arrays.asList("AESWRAP_128")
    );

    /*
*/
    public List<String> get_supported_algorithm_modes(String algo) {
        return this.encrypt_providers.keySet().stream()
                .filter(x -> x.startsWith(algo))
                .map(z -> z.split("/").length > 1 ? z.split("/")[1] : z.split("/")[0])
                .collect(Collectors.toList());
    }

    public List<String> get_supported_algorithm_padds(String algo, String mode) {
        return this.encrypt_providers.keySet().stream()
                .filter(x -> x.startsWith(String.format("%s/%s", algo, mode)))
                .map(z -> z.split("/")[2])
                .collect(Collectors.toList());
    }

    public Set<String> get_providers_supporting_combo(String algo, String mode, String paddingmode) {
        return this.encrypt_providers.get(String.format("%s/%s/%s", algo, mode, paddingmode));
    }

    public static SecretKey getKey(String algo, int keylen, String mode, String padding, String provider) {
        try {
            Method method = getMethod(SymmetricKeyGen.class.getName(),
                    String.format("gen_key_%s_%s", algo, provider),
                    new Class[]{int.class, String.class, String.class});
            return (SecretKey) method.invoke(null, new Object[]{keylen, mode, padding});

        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

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

    public  Map.Entry<String, IvParameterSpec> encrypt(String plaintext, Key key,String algo, String provider){
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            cipher = Cipher.getInstance(algo, provider);
            cipher.init(Cipher.ENCRYPT_MODE, key);
            ciphertext = cipher.doFinal(plaintext.getBytes());
            return new AbstractMap.SimpleEntry<>(byteArrayToStringBase64(ciphertext), new IvParameterSpec(new byte[]{}));
        } catch (NoSuchProviderException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | UnsupportedOperationException | BadPaddingException e) {
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
    public static Map.Entry<String, IvParameterSpec> encrypt_ChaCha20Poly(String msg, String mode,
                                                                          String padding,
                                                                          Key key,
                                                                          String provider){
        /* if (input.length == 0) {
            throw new IllegalArgumentException("Length of message cannot be 0");
        }
        if (key.getEncoded().length * 8 != KEY_LEN) {
            throw new IllegalArgumentException("Size of key must be 256 bits");
        }
        */
        //Cipher cipher = Cipher.getInstance("ChaCha20-Poly1305/None/NoPadding");

        int NONCE_LEN = 12;
        byte[] nonce = new byte[12]; // getNonce(); avoid
        IvParameterSpec ivParameterSpec = new IvParameterSpec(nonce);
        try{
            Cipher cipher = Cipher.getInstance("ChaCha20/Poly1305/NoPadding");
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