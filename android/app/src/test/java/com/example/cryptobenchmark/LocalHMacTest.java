package com.example.cryptobenchmark;

import com.example.cryptobenchmark.benchmark.preparation.workload.StringType;

import org.junit.Test;

import java.util.Map;
import java.util.Set;

import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_MD5;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA1;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA224;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA256;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA384;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA512;
import static org.junit.Assert.assertNotNull;

public class LocalHMacTest {

    
    public void testHMACMD5() {
        String msg = (String) StringType.genRandomWithSize(255).getValue();
        String key = (String) StringType.genRandomWithSize(128).getValue();
        String res = mac_MD5(msg, key);
        assertNotNull(res);
    }

    
    public void testHMACSHA1() {
        String msg = (String) StringType.genRandomWithSize(255).getValue();
        String key = (String) StringType.genRandomWithSize(128).getValue();
        String res = mac_SHA1(msg, key);
        assertNotNull(res);
    }

    
    public void testHMACSHA224() {
        String msg = (String) StringType.genRandomWithSize(255).getValue();
        String key = (String) StringType.genRandomWithSize(128).getValue();
        String res = mac_SHA224(msg, key);
        assertNotNull(res);
    }

    
    public void testHMACSHA256() {
        String msg = (String) StringType.genRandomWithSize(255).getValue();
        String key = (String) StringType.genRandomWithSize(128).getValue();
        String res = mac_SHA256(msg, key);
        assertNotNull(res);
    }

    
    public void testHMACSHA384() {
        String msg = (String) StringType.genRandomWithSize(255).getValue();
        String key = (String) StringType.genRandomWithSize(128).getValue();
        String res = mac_SHA384(msg, key);
        assertNotNull(res);
    }

    
    public void testHMACSHA512() {
        String msg = (String) StringType.genRandomWithSize(255).getValue();
        String key = (String) StringType.genRandomWithSize(128).getValue();
        String res = mac_SHA512(msg, key);
        assertNotNull(res);
    }

}
