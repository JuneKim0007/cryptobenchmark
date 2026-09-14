package com.example.cryptobenchmark;

import java.util.Map;

import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;

import com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricEncrypt;
import com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricDecrypt;
import com.example.cryptobenchmark.setup.CryptoPrimitive;
import com.example.cryptobenchmark.setup.CryptoProvider;
import com.example.cryptobenchmark.setup.DeviceCryptoPrimitives;
import static com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric.AssymmetricEncryptKeyGen.gen_dsa_key;
import static com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric.AssymmetricEncryptKeyGen.gen_key_ECDSA;
import static com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricKeyGen.gen_key_AES;
import static com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricKeyGen.gen_key_AES_AndroidKeyStore;
import static com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricKeyGen.gen_key_BLOWFISH;
import static com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricKeyGen.gen_key_ChaCha20;
import static com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricKeyGen.gen_key_DES;
import com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricKeyGen;
import com.example.cryptobenchmark.crypto.primitive.cipher.DecryptOperation;
import com.example.cryptobenchmark.crypto.primitive.cipher.EncryptOperation;
import com.example.cryptobenchmark.crypto.primitive.cipher.asymmetric.AssymmetricEncryptKeyGen;
import com.example.cryptobenchmark.misc.datatypes.DataType;
import com.example.cryptobenchmark.misc.datatypes.StringType;
import org.junit.Test;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertEquals;

public class LocalSymmetricTest {

    
    public void testEncryptAll() {
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        SymmetricEncrypt se = new SymmetricEncrypt(de);
    }

    @Test
    public void testEncrypt() {
        String provider = "SunJCE";
        DeviceCryptoPrimitives de = new DeviceCryptoPrimitives();
        SymmetricEncrypt se = new SymmetricEncrypt(de);
        String msg = (String) StringType.genRandomWithSize(128).getValue();
        System.out.println("Message: " + msg + " - " + msg.length());
        SecretKey secret = SymmetricKeyGen.gen_key_AES(128,"ECB","NOPADDING");
        assertNotNull(secret);
        // encrypt_AES(String message, String mode, String padding, Key key, String provider) {
        Map.Entry<String, IvParameterSpec> res  = SymmetricEncrypt.encrypt_AES(msg ,"ECB","NOPADDING", secret, provider);
        System.out.println("Message: " + res.getKey() + " - " + res.getKey().length());
        assertNotNull(res.getKey());
        // decrypt_AES(String message, String mode, String padding, Key key, String provider, IvParameterSpec iv){
        String decrypted_plaintext = SymmetricDecrypt.decrypt_AES(res.getKey(), "ECB", "NOPADDING", secret, provider, res.getValue());
        assertEquals(msg,decrypted_plaintext);
    }
}
