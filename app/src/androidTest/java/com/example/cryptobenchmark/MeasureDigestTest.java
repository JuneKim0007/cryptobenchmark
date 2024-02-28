package com.example.cryptobenchmark;

import androidx.test.runner.AndroidJUnit4;

import com.example.cryptobenchmark.digest.Digest;
import com.example.cryptobenchmark.digest.DigestOperation;
import com.example.cryptobenchmark.misc.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.misc.datatypes.StringType;
import com.hunter.library.debug.HunterDebug;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

/**
 * Instrumented test, which will execute on an Android device.
 *
 * @see <a href="http://d.android.com/tools/testing">Testing documentation</a>
 */
@RunWith(AndroidJUnit4.class)
public class MeasureDigestTest extends MeasureTest{

    public void digest(DigestOperation digest, String provider){
        for (int i = 0; i < nTimes; i++) {
            String param = INPUT_MESSAGES[ i % INPUT_MESSAGES.length];
            digest.digest(param, provider);
        }
    }

    public void digest(DigestOperation digest){
        //System.out.println("Digesting " + INPUT_MESSAGES.length + " messages " + nTimes + " times");
        for (int i = 0; i < nTimes; i++) {
            String param = INPUT_MESSAGES[ i % INPUT_MESSAGES.length];
            digest.digest(param, PROVIDER);
        }
    }
    
    @Test
    @HunterDebug
    public void test_md5_BC(){
        String provider = "BC";
        DigestOperation dop = Digest::digest_MD5;
        digest(dop, provider);
    }

    
    @Test
    @HunterDebug
    public void test_sha1_BC(){
        String provider = "BC";
        DigestOperation dop = Digest::digest_SHA1;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_sha224_BC(){
        String provider = "BC";
        DigestOperation dop = Digest::digest_SHA224;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_sha256_BC(){
        String provider = "BC";
        DigestOperation dop = Digest::digest_SHA256;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_sha384_BC(){
        String provider = "BC";
        DigestOperation dop = Digest::digest_SHA384;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_sha512_BC(){
        String provider = "BC";
        DigestOperation dop = Digest::digest_SHA512;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_md5_AndroidOpenSSL(){
        String provider = "AndroidOpenSSL";
        DigestOperation dop = Digest::digest_MD5;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_sha1_AndroidOpenSSL(){
        String provider = "AndroidOpenSSL";
        DigestOperation dop = Digest::digest_SHA1;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_sha224_AndroidOpenSSL(){
        String provider = "AndroidOpenSSL";
        DigestOperation dop = Digest::digest_SHA224;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_sha256_AndroidOpenSSL(){
        String provider = "AndroidOpenSSL";
        DigestOperation dop = Digest::digest_SHA256;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_sha384_AndroidOpenSSL(){
        String provider = "AndroidOpenSSL";
        DigestOperation dop = Digest::digest_SHA384;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_sha512_AndroidOpenSSL(){
        String provider = "AndroidOpenSSL";
        DigestOperation dop = Digest::digest_SHA512;
        digest(dop, provider);
    }

    
    @Test
@HunterDebug
    public void test_md5(){
        DigestOperation dop = Digest::digest_MD5;
        digest(dop, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sha1(){
        DigestOperation dop = Digest::digest_SHA1;
        digest(dop, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sha224(){
        DigestOperation dop = Digest::digest_SHA224;
        digest(dop, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sha256(){
        DigestOperation dop = Digest::digest_SHA256;
        digest(dop, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sha384(){
        DigestOperation dop = Digest::digest_SHA384;
        digest(dop, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_sha512(){
        DigestOperation dop = Digest::digest_SHA512;
        digest(dop, PROVIDER);
    }

    
    @Test
@HunterDebug
    public void test_md5_default(){
        DigestOperation dop = Digest::digest_MD5;
        digest(dop);
    }

    
    @Test
@HunterDebug
    public void test_sha1_default(){
        DigestOperation dop = Digest::digest_SHA1;
        digest(dop);
    }

    
    @Test
@HunterDebug
    public void test_sha224_default(){
        DigestOperation dop = Digest::digest_SHA224;
        digest(dop);
    }

    
    @Test
@HunterDebug
    public void test_sha256_default(){
        DigestOperation dop = Digest::digest_SHA256;
        digest(dop);
    }

    
    @Test
@HunterDebug
    public void test_sha384_default(){
        DigestOperation dop = Digest::digest_SHA384;
        digest(dop);
    }

    
    @Test
@HunterDebug
    public void test_sha512_default(){
        DigestOperation dop = Digest::digest_SHA512;
        digest(dop);
    }
}