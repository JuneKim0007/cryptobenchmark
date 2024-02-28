package com.example.cryptobenchmark;

import com.example.cryptobenchmark.decrypt.symmetric.DecryptOperation;
import com.example.cryptobenchmark.encrypt.symmetric.EncryptOperation;
import com.example.cryptobenchmark.keygen.assymmetric.AssymmetricEncryptKeyGen;
import com.example.cryptobenchmark.misc.datatypes.DataType;
import com.example.cryptobenchmark.misc.datatypes.StringType;

import org.junit.After;
import org.junit.Before;

import java.security.InvalidAlgorithmParameterException;
import java.security.Key;
import java.security.KeyPair;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;

import static com.example.cryptobenchmark.keygen.assymmetric.AssymmetricEncryptKeyGen.gen_dsa_key;
import static com.example.cryptobenchmark.keygen.assymmetric.AssymmetricEncryptKeyGen.gen_key_ECDSA;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_AES;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_AES_AndroidKeyStore;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_BLOWFISH;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_ChaCha20;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_DES;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_ARC4;
import static com.example.cryptobenchmark.misc.Utils.getConfigs;

public class MeasureTest {

    public static Map <String, String> configs = getConfigs();
    public static int inputSize = Integer.parseInt(configs.containsKey("INPUT_SIZE") ? configs.get("INPUT_SIZE") : BuildConfig.INPUT_SIZE);
    public static int keyLen = Integer.parseInt(configs.containsKey("KEY_LEN") ? configs.get("KEY_LEN") : BuildConfig.KEY_LEN); // Integer.parseInt(BuildConfig.KEY_LEN);
    public static int nTimes = Integer.parseInt(configs.containsKey("N_TIMES") ? configs.get("N_TIMES") : BuildConfig.N_TIMES); //Integer.parseInt(BuildConfig.N_TIMES);
    public static int warmup_time = Integer.parseInt(configs.containsKey("WARM_UP_TIME") ? configs.get("WARM_UP_TIME") : BuildConfig.WARM_UP_TIME); //Integer.parseInt(BuildConfig.WARM_UP_TIME);
    public static int cool_down_time = Integer.parseInt(configs.containsKey("COOL_DOWN_TIME") ? configs.get("COOL_DOWN_TIME") : BuildConfig.COOL_DOWN_TIME); //Integer.parseInt(BuildConfig.COOL_DOWN_TIME);
    public static String PROVIDER = configs.containsKey("PROVIDER") ? configs.get("PROVIDER") : BuildConfig.PROVIDER; // //BuildConfig.PROVIDER;
    public static String ALGORITHM = configs.containsKey("ALGORITHM") ? configs.get("ALGORITHM") : BuildConfig.ALGORITHM; // BuildConfig.ALGORITHM;
    public static String MODE = configs.containsKey("MODE") ? configs.get("MODE") : BuildConfig.MODE; // BuildConfig.MODE;
    public static String PADDING = configs.containsKey("PADDING") ? configs.get("PADDING") : BuildConfig.PADDING; //BuildConfig.PADDING;
    public static boolean WITH_KEY_SPEC = Integer.parseInt(configs.containsKey("WITH_KEY_SPEC") ? configs.get("WITH_KEY_SPEC") : BuildConfig.WITH_KEY_SPEC) == 1; // Integer.parseInt(BuildConfig.WITH_KEY_SPEC) == 1;
    public static int SAFETY_THRESHOLD = 3;
    public static int STACK_SIZE_LIM = (16 - SAFETY_THRESHOLD) * 1024; // 16KB - safe threshold (16- thsold);
    public static String[] INPUT_MESSAGES =  gen_random_workload(inputSize, nTimes);


    public static void encrypt_decrypt(EncryptOperation so, DecryptOperation sdo,
                                       Key sk, String[] params,
                                       String provider, String padding, String mode) throws Exception {
        for (int i = 0; i < nTimes; i++) {
            String param = params[ i % params.length];
            Map.Entry<String, IvParameterSpec> res = so.encrypt(param, mode, padding, sk, provider);
            String originaltext = sdo.decrypt(res.getKey(), mode, padding, sk, provider, res.getValue());
            if(! originaltext.equals(param)){
                throw new Exception("original message does not match final result");
            }
        }
    }

    public static void encrypt_decrypt(EncryptOperation so, DecryptOperation sdo,
                                       Key pk, Key sk, String[] params,
                                       String provider, String padding, String mode) throws Exception {
        for (int i = 0; i < nTimes; i++) {
            String param = params[ i % params.length];
            Map.Entry<String, IvParameterSpec> res = so.encrypt(param, mode, padding, pk, provider);
            String originaltext = sdo.decrypt(res.getKey(), mode, padding, sk, provider, res.getValue());
            if(! originaltext.equals(param)){
                throw new Exception("original message does not match final result");
            }
        }
    }

    public static void decrypt(DecryptOperation sdo,
                               Key sk, List<Map.Entry<String, IvParameterSpec>> cyphered_stuff,
                               String provider, String padding, String mode) throws Exception {
        for (int i = 0; i < cyphered_stuff.size() ; i++) {
            String originaltext = sdo.decrypt(cyphered_stuff.get(i).getKey(), mode, padding, sk, provider,
                    cyphered_stuff.get(i).getValue());
            if(! originaltext.equals(INPUT_MESSAGES[i])){
                throw new Exception("original message does not match final result");
            }
        }
    }

    public static void encrypt(EncryptOperation so, Key pk, String[] params, String provider,
                               String padding, String mode) throws Exception {
        for (int i = 0; i < nTimes; i++) {
            String param = params[ i % params.length];
            Map.Entry<String, IvParameterSpec> res = so.encrypt(param, mode, padding, pk, provider);
            if(res.getKey() == null){
                throw new Exception("cyphertext is null");
            }
        }
    }



    public static void encrypt_symmetric(EncryptOperation so, SecretKey sk, String[] params,
                                         String provider, String padding, String mode) throws Exception {
        for (int i = 0; i < nTimes; i++) {
            String param = params[ i % params.length];
            Map.Entry<String, IvParameterSpec> res = so.encrypt(param, mode, padding, sk, provider);
            if(res.getKey() == null){
                throw new Exception("cyphered text is null");
            }
        }
    }

    public static void assertExecution(String algo, String mode, String padding, String provider) throws Exception {
        boolean should_not_run = !algo.equalsIgnoreCase(ALGORITHM)
                && (!PROVIDER.equalsIgnoreCase("ALL") ||  !provider.equalsIgnoreCase(PROVIDER))
                    && (!mode.equals("") || !mode.equalsIgnoreCase(MODE))
                        && (!padding.equals("") || !padding.equalsIgnoreCase(PADDING));
        if (should_not_run){
            throw new Exception("Skipping execution");
        }
    }

    public SecretKey gen_symmetric_key(String algo, int keyLen,
                                       String provider, String mode, String padding) {
        if (algo.toLowerCase().contains("chacha20")){
            return gen_key_ChaCha20(keyLen, provider);
        }
        if (algo.toLowerCase().contains("blowfish")){
            return gen_key_BLOWFISH(keyLen, provider);
        }
        else if (algo.equalsIgnoreCase("des")){
            return  gen_key_DES(keyLen, mode, padding, provider);
        }
        else if (algo.equalsIgnoreCase("3des")
                || algo.equalsIgnoreCase("desede")){
            return  gen_key_DES(keyLen, mode, padding, provider);
        }
        else if (algo.equalsIgnoreCase("aes")){
            if (provider.toLowerCase().contains("androidkeystore")){
                return  gen_key_AES_AndroidKeyStore(keyLen, mode, padding);
            }
            else{
                return gen_key_AES(keyLen, mode, padding, provider);
            }
        }
        else if (algo.equalsIgnoreCase("rc4")){
            return gen_key_ARC4(keyLen, provider);
        }

        return null;
    }

    public static KeyPair gen_key_pair(int keyLen, String algorithm, String provider,
                                       String mode, String padding, boolean withKeySpec){
        try {
            if (provider.toLowerCase().contains("androidkeystore")){
                if(algorithm.toLowerCase().contains("rsa")){
                    if (withKeySpec){
                        return AssymmetricEncryptKeyGen.gen_key_rsakeyspec(keyLen, mode,
                                padding, provider);
                    }
                    return AssymmetricEncryptKeyGen.gen_key_RSA(keyLen, mode, padding);
                }
                else if(algorithm.toLowerCase().contains("dsa")){
                    return gen_dsa_key(keyLen);
                }
                else if(algorithm.toLowerCase().contains("ecdsa")){
                    return gen_key_ECDSA(keyLen);
                }
            }
            else {
                if(algorithm.toLowerCase().contains("rsa")){
                    return AssymmetricEncryptKeyGen.gen_key_RSA(keyLen);
                }
                else if(algorithm.toLowerCase().contains("dsa")){
                    return gen_dsa_key(keyLen);
                }
                else if(algorithm.toLowerCase().contains("ecdsa")){
                    return gen_key_ECDSA(keyLen);
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    @Before
    public void before_tests(){
        try {
            System.out.println("before");
            Thread.sleep(warmup_time);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    @After
    public void after_tests(){
        try {
            System.out.println("after");
            Thread.sleep(cool_down_time);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public static String[] gen_random_workload(int size, int times){
        int bytes_per_char = 2;
        System.out.println(" size: " + size + " times: " + times + " STACK_SIZE_LIM: " + STACK_SIZE_LIM + "");
        //int max_times  = times % (STACK_SIZE_LIM / (size * bytes_per_char) );
        int max_times  = (int) Math.floor(STACK_SIZE_LIM / (size * bytes_per_char));
        String[] res = new String[max_times];
        System.out.println("max_times: " + max_times + " size: " + size + " times: " + times + " STACK_SIZE_LIM: " + STACK_SIZE_LIM + "");
        DataType[] dt = StringType.genRandomWithSize(size, max_times);
        for (int i = 0; i < dt.length; i++) {
            res[i] = ((String) dt[i].getValue());
            //System.out.println("res[i]: " + res[i]);
            //System.out.println("res[i] size in bytes: " + res[i].getBytes().length);
        }
        return res;
    }

    public static boolean istheSelectedProvider(String providerId){
        return PROVIDER.toLowerCase().equals(providerId.toLowerCase());
    }

}
