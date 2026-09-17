package io.github.junekim0007.cryptobench;

import androidx.test.runner.AndroidJUnit4;

import io.github.junekim0007.cryptobench.crypto.primitive.cipher.symmetric.SymmetricDecrypt;
import io.github.junekim0007.cryptobench.crypto.primitive.cipher.DecryptOperation;
import com.hunter.library.debug.HunterDebug;
import org.junit.Test;
import org.junit.runner.RunWith;
import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;


@RunWith(AndroidJUnit4.class)
public class MeasureSymmetricDecryptTest extends MeasureTest {

    public static IvParameterSpec iv = new IvParameterSpec(new byte[8]);
    String[] params = MeasureTest.INPUT_MESSAGES;
    SecretKey SECRET_KEY = gen_symmetric_key(ALGORITHM, keyLen, PROVIDER, MODE, PADDING);


    public static void decrypt(DecryptOperation sdo, SecretKey sk, String[] params,
                               String provider, String padding, String mode, IvParameterSpec iv) throws Exception {
        for (String param : params) {
            String res = sdo.decrypt(param, mode, padding, sk, provider, iv);
            if (res == null) {
                throw new Exception("decyphered text is null");
            }
        }
    }

    // CHACHA20
    
    @Test
@HunterDebug
    public void test_CHA_CHA_20_AndroidOpenSSL() throws Exception {
        String algo = "ChaCha20";
        String provider = "AndroidOpenSSL";
        String padd = "";
        String mode = "";
        DecryptOperation deo = SymmetricDecrypt::decrypt_ChaCha20;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    
    @Test
@HunterDebug
    public void test_CHA_CHA_20() throws Exception {
        DecryptOperation deo = SymmetricDecrypt::decrypt_ChaCha20;
        decrypt(deo, SECRET_KEY, params, PROVIDER, PADDING, MODE, iv);
    }

    // DES/ECB/PKCS5PADDING

    // AES GCM
    @Test
@HunterDebug
    
    public void test_AES_GCM_NoPadding_AndroidKeyStore() throws Exception {
        String mode = "GCM";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_AES_GCM_NoPadding_AndroidOpenSSL() throws Exception {
        String mode = "GCM";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    // AES GCM - SIV

    @Test
@HunterDebug
    
    public void test_AES_GCM_siv_NoPadding_AndroidOpenSSL() throws Exception {
        String mode = "GCM-SIV";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    // CBC

    @Test
@HunterDebug
    
    public void test_AES_CBC_NoPadding_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_AES_CBC_PKCS7Padding_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS7PADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_AES_CBC_PKCS5Padding_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS5PADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_AES_ECB_NOPADDING_AndroidOpenSSL() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_AES_ECB_NOPADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }


    @Test
@HunterDebug
    
    public void test_AES_ECB_PKCS5PADDING_AndroidOpenSSL() throws Exception {
        String mode = "ECB";
        String padd = "PKCS5PADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_AES_ECB_PKCS7PADDING_AndroidOpenSSL() throws Exception {
        String mode = "ECB";
        String padd = "PKCS7PADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    // CTR NO padding

    @Test
@HunterDebug
    
    public void test_AES_CTR_NOPADDING_AndroidOpenSSL() throws Exception {
        String mode = "CTR";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_AES_CTR_NOPADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "CTR";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_AES() throws Exception {
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        decrypt(deo, SECRET_KEY, params, PROVIDER, PADDING, MODE, iv);
    }

    // DES - ECB

    @Test
@HunterDebug
    
    public void test_DES_ECB_NOPADDING_BC() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_DES_ECB_PKCS5PADDING_BC() throws Exception {
        String mode = "ECB";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_DES_ECB_PKCS7PADDING_BC() throws Exception {
        String mode = "ECB";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    // DES - CTR
    @Test
@HunterDebug
    
    public void test_DES_CTR_NOPADDING_BC() throws Exception {
        String mode = "CTR";
        String padd = "NOPADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_DES_CTR_PKCS5PADDING_BC() throws Exception {
        String mode = "CTR";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_DES_CTR_PKCS7PADDING_BC() throws Exception {
        String mode = "CTR";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    // DES - CBC

    @Test
@HunterDebug
    
    public void test_DES_CBC_NOPADDING_BC() throws Exception {
        String mode = "CBC";
        String padd = "NOPADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_DES_CBC_PKCS5PADDING_BC() throws Exception {
        String mode = "CBC";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_DES_CBC_PKCS7PADDING_BC() throws Exception {
        String mode = "CBC";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    // DES - OFB

    @Test
@HunterDebug
    
    public void test_DES_OFB_NOPADDING_BC() throws Exception {
        String mode = "OFB";
        String padd = "NOPADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_DES_OFB_PKCS5PADDING_BC() throws Exception {
        String mode = "OFB";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_DES_OFB_PKCS7PADDING_BC() throws Exception {
        String mode = "OFB";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_DES() throws Exception {
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        decrypt(deo, SECRET_KEY, params, PROVIDER, PADDING, MODE, iv);
    }

    // 3DES (DESEDE) - CBC

    @Test
@HunterDebug
    
    public void test_3DES_CBC_NOPADDING_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_3DES_CBC_PKCS5PADDING_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS5PADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_3DES_CBC_PKCS7PADDING_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS7PADDING";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    // 3DES (DESEDE) - CBC

    @Test
@HunterDebug
    
    public void test_3DES_ECB_NOPADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_3DES_ECB_PKCS7PADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "ECB";
        String padd = "PKCS7PADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_3DES() throws Exception {
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        decrypt(deo, SECRET_KEY, params, PROVIDER, PADDING, MODE, iv);
    }


    // ARC4

    @Test
@HunterDebug
    
    public void test_ARC4_BC() throws Exception {
        String mode = "";
        String padd = "";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_ARC4;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_ARC4_AndroidOpenSSL() throws Exception {
        String mode = "";
        String padd = "";
        String provider = "AndroidOpenSSL";
        DecryptOperation deo = SymmetricDecrypt::decrypt_ARC4;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    @Test
@HunterDebug
    
    public void test_ARC4() throws Exception {
        DecryptOperation deo = SymmetricDecrypt::decrypt_ARC4;
        decrypt(deo, SECRET_KEY, params, PROVIDER, PADDING, MODE, iv);
    }


    // BLOWFISH
    
    @Test
@HunterDebug
    public void test_BLOWFISH_BC() throws Exception {
        String mode = "";
        String padd = "";
        String provider = "BC";
        DecryptOperation deo = SymmetricDecrypt::decrypt_BLOWFISH;
        decrypt(deo, SECRET_KEY, params, provider, padd, mode, iv);
    }

    
    @Test
@HunterDebug
    public void test_BLOWFISH() throws Exception {
        String mode = "";
        String padd = "";
        DecryptOperation deo = SymmetricDecrypt::decrypt_BLOWFISH;
        decrypt(deo, SECRET_KEY, params, PROVIDER, padd, mode, iv);
    }

}