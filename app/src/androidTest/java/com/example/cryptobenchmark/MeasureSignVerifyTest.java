package com.example.cryptobenchmark;

import com.example.cryptobenchmark.misc.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.sign.Sign;
import com.example.cryptobenchmark.sign.SignOperation;
import com.example.cryptobenchmark.verify.Verify;
import com.example.cryptobenchmark.verify.VerifyOperation;
import com.hunter.library.debug.HunterDebug;
import org.junit.Test;
import java.security.KeyPair;

public class MeasureSignVerifyTest extends MeasureTest{

    // aks - Ec
    // bc - ecdh, dsa, shaXwithecdsa, shaXwithrsa
    // aossl - ecdh, shaXwithecdsa, shaXwithrsa
    // aksbcw - shaXwithrsa, shaXwithdsa,

    public static int KEY_LEN = keyLen; // keyLen;
    public static String CRYPTO_PROVIDER =  PROVIDER; // "AndroidOpenSSL"; //MeasureTest.provider;

    KeyPair KEY_PAIR = gen_key_pair(KEY_LEN, ALGORITHM, CRYPTO_PROVIDER, MODE, PADDING, WITH_KEY_SPEC);


    public static void sign_and_verify(SignOperation sop, VerifyOperation vop, String algo,
                                KeyPair kp, String provider) throws Exception {
        for (int i = 0; i < nTimes; i++) {
            String msg = INPUT_MESSAGES[ i % INPUT_MESSAGES.length];
            String signedMessage = sop.sign(msg, algo, kp.getPrivate(), provider);
            if (!vop.verify(msg, signedMessage, algo, kp.getPublic(), provider)){
                System.out.println(msg);
                throw new Exception("Invalid Signature");
            }
        }
    }

    @Test
    public void test_dummy(){
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        System.out.println(dcp);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA1WithRSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA1WithRSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA256WithRSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA256WithRSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA384WithRSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA384WithRSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithRSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA512WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA1WithDSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA1WithRSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA256WithDSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA256WithRSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA384WithDSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA384WithDSA", mode = "", padding = "", provider = "AndroidOpenSSL";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithDSA_AndroidOpenSSL() throws Exception {
        String algo = "SHA512WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA1WithRSA_BC() throws Exception {
        String algo = "SHA1WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA256WithRSA_BC() throws Exception {
        String algo = "SHA256WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA384WithRSA_BC() throws Exception {
        String algo = "SHA384WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithRSA_BC() throws Exception {
        String algo = "SHA512WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA1WithRSA() throws Exception {
        String algo = "SHA1WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA256WithRSA() throws Exception {
        String algo = "SHA256WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA384WithRSA() throws Exception {
        String algo = "SHA384WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithRSA() throws Exception {
        String algo = "SHA512WithRSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, PROVIDER);
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
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA224WithDSA_BC() throws Exception {
        String algo = "SHA224WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA256WithDSA_BC() throws Exception {
        String algo = "SHA256WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA384WithDSA_BC() throws Exception {
        String algo = "SHA384WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithDSA_BC() throws Exception {
        String algo = "SHA512WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, provider);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA1WithDSA() throws Exception {
        String algo = "SHA1WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA224WithDSA() throws Exception {
        String algo = "SHA224WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA256WithDSA() throws Exception {
        String algo = "SHA256WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA384WithDSA() throws Exception {
        String algo = "SHA384WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sign_SHA512WithDSA() throws Exception {
        String algo = "SHA512WithDSA", mode = "", padding = "", provider = "BC";
        SignOperation sop = Sign::sign;
        VerifyOperation vop = Verify::verify;
        sign_and_verify(sop, vop, algo, KEY_PAIR, PROVIDER);
    }

}
