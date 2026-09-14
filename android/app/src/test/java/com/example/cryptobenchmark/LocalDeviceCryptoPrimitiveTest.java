package com.example.cryptobenchmark;

import com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricEncrypt;
import com.example.cryptobenchmark.environment.discovery.CryptoPrimitive;
import com.example.cryptobenchmark.environment.discovery.CryptoProvider;
import com.example.cryptobenchmark.environment.discovery.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.benchmark.preparation.workload.StringType;
import org.junit.Test;

import java.util.List;
import java.util.Map;
import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;
import static com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricDecrypt.decrypt_AES;
import static com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricKeyGen.gen_key_AES;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;

public class LocalDeviceCryptoPrimitiveTest {


    
    public void testFileGen(){
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        assertNotNull(de);
    }

    
    public void testSpecificSymmetric(){
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        String msg = (String) StringType.genRandomWithSize(64).getValue();
        SecretKey pk = gen_key_AES(128 ,"", "", "SunJCE");
        Map.Entry<String, IvParameterSpec> m = SymmetricEncrypt.encrypt_AES(msg, "CBC", "NoPadding", pk, "SunJCE");
        assertNotNull(m);
        String plaintext = decrypt_AES(m.getKey(), "CBC", "NoPadding", pk, "SunJCE", m.getValue());
        assertEquals(msg,plaintext);
    }

    
    public void testAlgorithmListNotEmpty(){
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        assertNotEquals("Algorithms supported", de.getImplementedAlgorithms().size(), 0);
    }

    
    public void testAlgorithmSearch(){
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        CryptoProvider cp = de.getFirstProviderImplementingAlgorithm("AES");
        CryptoProvider cp2 = de.getFirstProviderImplementingAlgorithm("potato");
        assertNotNull(cp);
        assertNull(cp2);
    }

    
    public void testGetAlgorithmOfProvider(){
        String algorithm = "AES";
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        CryptoProvider cp = de.getFirstProviderImplementingAlgorithm(algorithm);
        assertNotNull(cp);
        CryptoPrimitive cpp = cp.getFirstImplementedPrimitive(algorithm);
        assertNotNull("has implementation of algorithm " + algorithm, cpp);
    }

}
