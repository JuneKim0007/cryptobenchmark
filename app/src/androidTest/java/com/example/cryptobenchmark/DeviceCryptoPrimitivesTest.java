package com.example.cryptobenchmark;

import android.content.Context;
import androidx.test.platform.app.InstrumentationRegistry;
import android.util.Log;

import com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricEncrypt;
import com.example.cryptobenchmark.setup.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.misc.datatypes.StringType;

import org.junit.Test;

import java.security.Provider;
import java.security.Security;
import java.util.Map;
import java.util.Set;

import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;

import static junit.framework.Assert.assertNotNull;

public class DeviceCryptoPrimitivesTest {

    @Test
    public void testFileLoadDevice(){
        Context ctx = InstrumentationRegistry.getInstrumentation().getTargetContext();
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives(ctx, false);
        assertNotNull(de);

    }

    @Test
    public void testFileGen(){
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        assertNotNull(de);
    }

    /*
    @Test
    public void testSymmetricWithFileGen(){
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        String msg = (String) StringType.genRandomWithSize(64).getValue();
        SymmetricEncrypt se = new SymmetricEncrypt(de);
        SecretKey pk = gen_key_AES_AndroidOpenSSL(128, "", "");
        Map<String, IvParameterSpec> m = se.encrypt_all(msg, "AES", pk,"AndroidOpenSSL");
    }*/
}
