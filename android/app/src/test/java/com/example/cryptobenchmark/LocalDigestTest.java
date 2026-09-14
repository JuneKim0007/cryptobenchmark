package com.example.cryptobenchmark;

import com.example.cryptobenchmark.environment.discovery.CryptoProvider;
import com.example.cryptobenchmark.environment.discovery.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.benchmark.preparation.workload.StringType;

import org.junit.Test;

import java.util.List;
import java.util.Map;
import java.util.Set;

import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_MD5;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA1;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA224;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA256;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA384;
import static com.example.cryptobenchmark.crypto.primitive.mac.HMAC.mac_SHA512;
import static org.junit.Assert.assertNotNull;

public class LocalDigestTest {

    
    public void test_get_digest_impls() {
        DeviceCryptoPrimitives dcp = new DeviceCryptoPrimitives();
        List<String> primitives = dcp.getImplementedAlgorithms();
        System.out.println();
    }



}
