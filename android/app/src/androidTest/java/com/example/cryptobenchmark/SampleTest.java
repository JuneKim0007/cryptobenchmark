package com.example.cryptobenchmark;

import com.example.cryptobenchmark.crypto.primitive.digest.Digest;
import com.example.cryptobenchmark.crypto.primitive.digest.DigestOperation;

import org.junit.Before;
import org.junit.Test;

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
}
