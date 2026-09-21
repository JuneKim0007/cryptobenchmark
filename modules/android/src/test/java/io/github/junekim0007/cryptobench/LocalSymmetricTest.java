package io.github.junekim0007.cryptobench;

import java.util.Map;

import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;

import io.github.junekim0007.cryptobench.crypto.primitive.cipher.symmetric.SymmetricEncrypt;
import io.github.junekim0007.cryptobench.crypto.primitive.cipher.symmetric.SymmetricDecrypt;
import static io.github.junekim0007.cryptobench.crypto.primitive.keygen.SymmetricKeyGen.gen_key_AES;
import static io.github.junekim0007.cryptobench.crypto.primitive.keygen.SymmetricKeyGen.gen_key_AES_AndroidKeyStore;
import static io.github.junekim0007.cryptobench.crypto.primitive.keygen.SymmetricKeyGen.gen_key_BLOWFISH;
import static io.github.junekim0007.cryptobench.crypto.primitive.keygen.SymmetricKeyGen.gen_key_ChaCha20;
import static io.github.junekim0007.cryptobench.crypto.primitive.keygen.SymmetricKeyGen.gen_key_DES;
import io.github.junekim0007.cryptobench.crypto.primitive.keygen.SymmetricKeyGen;
import io.github.junekim0007.cryptobench.crypto.primitive.cipher.DecryptOperation;
import io.github.junekim0007.cryptobench.crypto.primitive.cipher.EncryptOperation;
import io.github.junekim0007.cryptobench.crypto.primitive.keygen.AssymmetricEncryptKeyGen;
import io.github.junekim0007.cryptobench.preparation.workload.DataType;
import io.github.junekim0007.cryptobench.preparation.workload.StringType;
import org.junit.Test;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertEquals;

public class LocalSymmetricTest {

    
    public void testEncryptAll() {
    }

    @Test
    public void testEncrypt() {
        String provider = "SunJCE";
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
