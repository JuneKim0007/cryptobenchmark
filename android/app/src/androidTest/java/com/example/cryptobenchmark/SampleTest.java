package com.example.cryptobenchmark;

import com.example.cryptobenchmark.crypto.primitive.digest.Digest;
import com.example.cryptobenchmark.crypto.primitive.digest.DigestOperation;


import org.junit.Before;
import org.junit.Test;
import java.security.NoSuchAlgorithmException;
import java.security.Provider;
import java.security.Security;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.util.Log;

public class SampleTest {

    public static String PROVIDER = BuildConfig.PROVIDER;
    public static String msg = "aaaa";

    @Before
    public void befas(){
        System.out.println(PROVIDER);
    }

    @Test
    public void test_digest_family_sha224(){
        DigestOperation dop = Digest::digest_SHA224;
        String res = dop.digest(msg, PROVIDER);
        if (res.length() == 28){
            System.out.println("Sha-3 fam");
        }
        else{
            System.out.println("Sha-2 fam");
        }
    }

    @Test
    public void test_digest_family_sha256(){
        DigestOperation dop = Digest::digest_SHA256;
        String res = dop.digest(msg, PROVIDER);
        if (res.length() == 32){
            System.out.println("Sha-3 fam");
        }
        else{
            System.out.println("Sha-2 fam");
        }
    }

    @Test
    public void test_digest_family_sha384(){
        DigestOperation dop = Digest::digest_SHA384;
        String res = dop.digest(msg, PROVIDER);
        if (res.length() == 48){
            System.out.println("Sha-3 fam");
        }
        else{
            System.out.println("Sha-2 fam");
        }
    }

    @Test
    public void test_digest_family_sha512(){
        DigestOperation dop = Digest::digest_SHA512;
        String res = dop.digest(msg, PROVIDER);
        if (res.length() == 64){
            System.out.println("Sha-3 fam");
        }
        else{
            System.out.println("Sha-2 fam");
        }
    }

    @Test
    public void testShowProviders(){
        for (Provider provider : Security.getProviders()) {
            Log.d("ProviderInfo", "Name: " + provider.getName());
            Log.d("ProviderInfo", "Version: " + provider.getVersion());
            Log.d("ProviderInfo", "Info: " + provider.getInfo());
            Log.d("ProviderInfo", "--------------------------------");
        }
    }
}
