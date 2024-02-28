package com.example.cryptobenchmark;
import com.example.cryptobenchmark.misc.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.sign.Sign;
import com.example.cryptobenchmark.sign.SignOperation;
import com.hunter.library.debug.HunterDebug;
import org.junit.Test;

import java.security.AlgorithmParameters;
import java.security.KeyPair;
import java.security.PrivateKey;
import java.security.Signature;

import javax.crypto.Cipher;


public class MeasureSignTest extends MeasureTest{

    // aks - Ec
    // bc - ecdh, dsa, shaXwithecdsa, shaXwithrsa
    // aossl - ecdh, shaXwithecdsa, shaXwithrsa
    // aksbcw - shaXwithrsa, shaXwithdsa,

    public static int KEY_LEN = keyLen; // keyLen;
    public static String CRYPTO_PROVIDER =  PROVIDER; // "AndroidOpenSSL"; //MeasureTest.provider;

    KeyPair KEY_PAIR = gen_key_pair(KEY_LEN, ALGORITHM, CRYPTO_PROVIDER, MODE, PADDING, WITH_KEY_SPEC);


    public void sign(SignOperation sop, String algo, PrivateKey key, String provider) throws Exception {
        for (int i = 0; i < nTimes; i++) {
            String msg = INPUT_MESSAGES[ i % INPUT_MESSAGES.length];
            String res = sop.sign(msg, algo, key, provider);
            if (res==null){
                throw new Exception("Invalid Signature");
            }
        }
    }
/*
    @Test
@HunterDebug
    public void test_dummy(){
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        System.out.println(dcp);
    }*/

    //@Test
    //@HunterDebug
    public void get_impl() {
        String[] algoList = {
               "DSA"
        };
        String[] providerList = {"AndroidOpenSSL", "AndroidKeyStoreBCWorkaround", "BC",
                "AndroidKeyStore", "" };

        for(String algo: algoList){
            for(String prov: providerList) {
                try{
                    Signature md = prov.equals("") ? Signature.getInstance(algo) : Signature.getInstance(algo, prov);
                    md.getProvider().getServices().stream().filter(x -> x.getAlgorithm().contains("DSA")).forEach(x -> System.out.println(x.getAlgorithm()));
                    //AlgorithmParameters apm  = md.getParameters();
                    System.out.println(md.getAlgorithm());
                }catch (Exception e){
                    e.printStackTrace();
                }
            }
        }
    }

    
    @Test
    @HunterDebug
    public void test_sign_SHA1WithRSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA1WithRSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    @Test
    @HunterDebug
    public void test_sign_SHA224WithRSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA224WithRSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
    @HunterDebug
    public void test_sign_SHA256WithRSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA256WithRSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA384WithRSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA384WithRSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithRSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA512WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA1WithRSA_BC() throws Exception {
        String algo = "SHA1WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    @Test
    @HunterDebug
    public void test_sign_SHA224WithRSA_BC() throws Exception {
        String algo = "SHA224WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }
    
    @Test
    @HunterDebug
    public void test_sign_SHA256WithRSA_BC() throws Exception {
        String algo = "SHA256WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    @Test
    @HunterDebug
    public void test_sign_SHA384WithRSA_BC() throws Exception {
        String algo = "SHA384WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithRSA_BC() throws Exception {
        String algo = "SHA512WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    // default

    
    @Test
@HunterDebug
    public void test_sign_SHA1WithRSA() throws Exception {
        String algo = "SHA1WithRSA", mode = "", padding = "";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), PROVIDER);
    }

    @Test
    @HunterDebug
    public void test_sign_SHA224WithRSA() throws Exception {
        String algo = "SHA224WithRSA", mode = "", padding = "";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), PROVIDER);
    }


    
    @Test
    public void test_sign_SHA256WithRSA() throws Exception {
        String algo = "SHA256WithRSA", mode = "", padding = "";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), PROVIDER);
    }

    
    @Test
    @HunterDebug
    public void test_sign_SHA384WithRSA() throws Exception {
        String algo = "SHA384WithRSA", mode = "", padding = "";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithRSA() throws Exception {
        String algo = "SHA512WithRSA", mode = "", padding = "";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), PROVIDER);
    }


    /*
    
    @Test
@HunterDebug
    public void test_sign_ECDSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA256WithECDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        KeyPair kp =  gen_key_ECDSA(KEY_LEN); // gen_key_pair(KEY_LEN, algo, provider, padding,  mode);
        SignOperation sop = Sign::sign;
        sign(sop, algo, kp.getPrivate(), provider);
    }*/

    //
    // DSA
    //

    
    @Test
@HunterDebug
    public void test_sign_SHA1WithDSA_BC() throws Exception {
        String algo = "SHA1WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA224WithDSA_BC() throws Exception {
        String algo = "SHA224WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA256WithDSA_BC() throws Exception {
        String algo = "SHA256WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
    @HunterDebug
    public void test_sign_SHA384WithDSA_BC() throws Exception {
        String algo = "SHA384WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithDSA_BC() throws Exception {
        String algo = "SHA512WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA1WithDSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA1WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    @Test
    @HunterDebug
    public void test_sign_SHA224WithDSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA224WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }
    
    @Test
    @HunterDebug
    public void test_sign_SHA256WithDSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA256WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
    @HunterDebug
    public void test_sign_SHA384WithDSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA384WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }

    
    @Test
    public void test_sign_SHA512WithDSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA512WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), provider);
    }


    
    @Test
    @HunterDebug
    public void test_sign_SHA1WithDSA() throws Exception {
        String algo = "SHA1WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), PROVIDER);
    }

    @Test
    @HunterDebug
    public void test_sign_SHA224WithDSA() throws Exception {
        String algo = "SHA224WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), PROVIDER);
    }


    
    @Test
    @HunterDebug
    public void test_sign_SHA256WithDSA() throws Exception {
        String algo = "SHA256WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA384WithDSA() throws Exception {
        String algo = "SHA384WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithDSA() throws Exception {
        String algo = "SHA512WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        sign(sop, algo, KEY_PAIR.getPrivate(), PROVIDER);
    }


}
