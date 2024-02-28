package com.example.cryptobenchmark.encrypt.assymmetric;

import com.example.cryptobenchmark.keygen.assymmetric.AssymmetricEncryptKeyGen;
import com.example.cryptobenchmark.misc.CryptoPrimitive;
import com.example.cryptobenchmark.misc.CryptoProvider;
import com.example.cryptobenchmark.misc.DeviceCryptoPrimitives;
import java.nio.charset.StandardCharsets;
import java.lang.reflect.Method;
import java.security.InvalidAlgorithmParameterException;
import java.security.InvalidKeyException;
import java.security.Key;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.security.spec.MGF1ParameterSpec;
import java.util.AbstractMap;

import java.util.Arrays;
import java.util.Collections;
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
import javax.crypto.spec.OAEPParameterSpec;
import javax.crypto.spec.PSource;

import static com.example.cryptobenchmark.misc.Utils.byteArrayToString;
import static com.example.cryptobenchmark.misc.Utils.byteArrayToStringBase64;
import static com.example.cryptobenchmark.misc.Utils.getMethod;


public class AssymmetricEncrypt {

    Map<String, Set<String>> encrypt_providers = new HashMap<>();
    private static Set<String> assymmetric_primitives = new HashSet<>(
            Arrays.asList("RSA")
    );

    public AssymmetricEncrypt(DeviceCryptoPrimitives dcp){
        for (CryptoProvider cp : dcp.getDeviceProviders().values()){
            for (String algoId : assymmetric_primitives){
                List<String> matchingPrimitives =  cp.getProviderPrimitives().values().stream().filter(x -> x.getSimpleName().matches(algoId+".*")).map(CryptoPrimitive::getPrimitiveName).collect(Collectors.toList());
                for (String s : matchingPrimitives){
                    addPrimitive(s, cp.getProviderName());
                }
            }
        }
    }

    public void addPrimitive(String primitiveName, String primitiveProvider){
        if(this.encrypt_providers.containsKey(primitiveName)){
            this.encrypt_providers.get(primitiveName).add(primitiveProvider);
        }
        else{
            this.encrypt_providers.put(primitiveName, new HashSet<>(Collections.singletonList(primitiveProvider)));
        }
    }

    public List<String> get_supported_algorithm_modes(String algo) {
        return this.encrypt_providers.keySet().stream()
                .filter(x -> x.startsWith(algo))
                .map(z -> z.split("/").length > 1 ? z.split("/")[1]: "")
                .collect(Collectors.toList());
    }

    public List<String> get_supported_algorithm_padds(String algo, String mode) {
        return this.encrypt_providers.keySet().stream()
                .filter(x -> x.startsWith(String.format("%s/%s", algo, mode)))
                .map(z -> z.split("/").length > 2 ? z.split("/")[2]: "NOPADDING")
                .collect(Collectors.toList());
    }

    public Set<String> get_providers_supporting_combo(String algo, String mode, String paddingmode) {
        return this.encrypt_providers.get(String.format("%s/%s/%s", algo, mode, paddingmode));
    }



    public static SecretKey getKey(String algo, int keylen, String mode, String padding, String provider) {
        try {
            Method method = getMethod(AssymmetricEncryptKeyGen.class.getName(),
                    String.format("gen_key_%s_%s", algo, provider),
                    new Class[]{int.class, String.class, String.class});
            return (SecretKey) method.invoke(null, new Object[]{keylen, mode, padding});

        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static Map.Entry<String, IvParameterSpec> encrypt_RSA_ECB_NOPADDING(String message, String mode, String padding, Key key, String provider) {
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            cipher = Cipher.getInstance("RSA/ECB/NOPADDING", provider);
            cipher.init(Cipher.ENCRYPT_MODE, key);
            ciphertext = cipher.doFinal(message.getBytes(StandardCharsets.UTF_8));
            return new AbstractMap.SimpleEntry<>(byteArrayToString(ciphertext), new IvParameterSpec(new byte[]{}));

        } catch (NoSuchProviderException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | BadPaddingException e) {
            e.printStackTrace();
            return null;
        }
    }

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

    public static Map.Entry<String, IvParameterSpec> encrypt_RSA_maloco(String message, String mode, String padding, Key key, String provider) {
        Cipher cipher = null;
        byte[] ciphertext = null;
        try {
            cipher = Cipher.getInstance(String.format("RSA/%s/%s", mode, padding), provider);
            cipher.init(Cipher.ENCRYPT_MODE, key, new OAEPParameterSpec("SHA-1", "MGF1", MGF1ParameterSpec.SHA1, PSource.PSpecified.DEFAULT));
            ciphertext = cipher.doFinal(message.getBytes(StandardCharsets.UTF_8));
            return new AbstractMap.SimpleEntry<>(byteArrayToString(ciphertext), new IvParameterSpec(new byte[8]));

        } catch (NoSuchProviderException | NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | BadPaddingException | InvalidAlgorithmParameterException e) {
            e.printStackTrace();
            return null;
        }
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