package com.example.cryptobenchmark;

import com.example.cryptobenchmark.crypto.primitive.mac.HMAC;
import com.example.cryptobenchmark.crypto.primitive.mac.HMACOperation;
import com.example.cryptobenchmark.setup.CryptoProvider;
import com.example.cryptobenchmark.setup.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.misc.datatypes.DataType;
import com.example.cryptobenchmark.misc.datatypes.StringType;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.crypto.Mac;

import static com.example.cryptobenchmark.DigestTest.gen_random_workload;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_MD5;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA1;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA224;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA256;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA384;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA512;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;

public class HMacTest {

    public static int inputSize = Integer.parseInt(BuildConfig.INPUT_SIZE);
    public static int keyLen = Integer.parseInt(BuildConfig.KEY_LEN);
    public static int nTimes = Integer.parseInt(BuildConfig.N_TIMES);
    public static int warmup_time = Integer.parseInt(BuildConfig.WARM_UP_TIME);
    public static int cool_down_time = Integer.parseInt(BuildConfig.COOL_DOWN_TIME);
    public static String provider =BuildConfig.PROVIDER;
    public static String[] inputs =  gen_random_workload(inputSize, nTimes);



    @Test
    public void test_get_Macimpl() {
        String[] algoList = {
                //"MD5", "SHA1", "SHA224", "SHA256", "SHA384" ,"SHA512"
                "HMACMD5", "HMACSHA1", "HMACSHA224", "HMACSHA256", "HMACSHA384" ,"HMACSHA512"
        };
        String[] providerList = {"AndroidOpenSSL", "AndroidKeyStoreBCWorkaround", "BC",

                "AndroidKeyStore", "" };

        for(String algo: algoList){
            for(String prov: providerList) {
                try{

                    //MessageDigest md = prov.equals("") ? java.security.MessageDigest.getInstance(algo) : java.security.MessageDigest.getInstance(algo, prov);
                    Mac md = prov.equals("") ? Mac.getInstance(algo) : Mac.getInstance(algo, prov);
                    String pevides =  md.getProvider().getName();
                    System.out.println("lulas: " + md.getAlgorithm());
                }catch (Exception e){
                    e.printStackTrace();
                }
            }
        }
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
        String[] res = new String[times];
        DataType[] dt = StringType.genRandomWithSize(size, times);
        for (int i = 0; i < dt.length; i++) {
            res[i] = ((String) dt[i].getValue());
        }
        return res;
    }

    public void exec_hmac(HMACOperation ho, String key, String[] params){
        for (int i = 0; i < params.length ; i++) {
            ho.do_hmac(key, params[i], "");
        }
    }

    public void exec_hmac() {
        String algo = "HMAC";
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        Map<String, Set<CryptoProvider>> cps =  de.getProvidersImplementingAlgorithm(algo);
        System.out.println(cps);
    }

    @Test
    public void test_get_dig_impls() {
        String algo = "SHA";
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        Map<String, Set<CryptoProvider>> cps =  de.getProvidersImplementingAlgorithm(algo);
        System.out.println(cps);
    }

    @Test
    public void test_all_impls() {
        DeviceCryptoPrimitives dce = new DeviceCryptoPrimitives();
        dce.removeProvider("BC");
        dce.removeProvider("AndroidKeyStore");
        dce.removeProvider("AndroidKeyStoreBCWorkaround");
        HMAC mc  = new HMAC(dce);
        String msg = (String) StringType.genRandomWithSize(inputSize).getValue();
        String key = (String) StringType.genRandomWithSize(keyLen).getValue();
        List<String> res = mc.mac_all(msg, key);
        assertNotEquals(res.size(), 0);
    }


    @Test
    public void testHMACMD5() {
        String msg = (String) StringType.genRandomWithSize(inputSize).getValue();
        String key = (String) StringType.genRandomWithSize(keyLen).getValue();
        String res = mac_MD5(msg, key);
        assertNotNull(res);
    }

    @Test
    public void testHMACSHA1() {
        String msg = (String) StringType.genRandomWithSize(inputSize).getValue();
        String key = (String) StringType.genRandomWithSize(keyLen).getValue();
        String res = mac_SHA1(msg, key);
        assertNotNull(res);
    }

    @Test
    public void testHMACSHA224() {
        String msg = (String) StringType.genRandomWithSize(inputSize).getValue();
        String key = (String) StringType.genRandomWithSize(keyLen).getValue();
        String res = mac_SHA224(msg, key);
        assertNotNull(res);
    }

    @Test
    public void testHMACSHA256() {
        String msg = (String) StringType.genRandomWithSize(inputSize).getValue();
        String key = (String) StringType.genRandomWithSize(keyLen).getValue();
        String res = mac_SHA256(msg, key);
        assertNotNull(res);
    }

    @Test
    public void testHMACSHA384() {
        String msg = (String) StringType.genRandomWithSize(inputSize).getValue();
        String key = (String) StringType.genRandomWithSize(keyLen).getValue();
        String res = mac_SHA384(msg, key);
        assertNotNull(res);
    }

    @Test
    public void testHMACSHA512() {
        String msg = (String) StringType.genRandomWithSize(inputSize).getValue();
        String key = (String) StringType.genRandomWithSize(keyLen).getValue();
        String res = mac_SHA512(msg, key);
        assertNotNull(res);
    }

    @Test
    public void testHMACSHA512OP() {
        String[] msgs = gen_random_workload(inputSize, nTimes);
        String key = (String) StringType.genRandomWithSize(keyLen).getValue();
        HMACOperation hmo = HMAC::mac_SHA512;
        exec_hmac(hmo, key, msgs);
    }
}
