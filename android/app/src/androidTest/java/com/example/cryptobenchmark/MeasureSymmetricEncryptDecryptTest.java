package com.example.cryptobenchmark;

import com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricDecrypt;
import com.example.cryptobenchmark.crypto.primitive.cipher.DecryptOperation;
import com.example.cryptobenchmark.crypto.primitive.cipher.symmetric.SymmetricEncrypt;
import com.example.cryptobenchmark.crypto.primitive.cipher.EncryptOperation;
import com.hunter.library.debug.HunterDebug;
import org.junit.Test;
import javax.crypto.SecretKey;

public class MeasureSymmetricEncryptDecryptTest extends MeasureTest {
    String[] INPUT_PARAMS = MeasureTest.INPUT_MESSAGES;
    SecretKey SECRET_KEY = gen_symmetric_key(ALGORITHM, keyLen, PROVIDER, MODE, PADDING);

    // CHACHA20
    
    @Test
@HunterDebug
    public void test_CHA_CHA_20_AndroidOpenSSL() throws Exception {
        String provider = "AndroidOpenSSL";
        String padd = "";
        String mode = "";
        EncryptOperation so = SymmetricEncrypt::encrypt_ChaCha20;
        DecryptOperation deo = SymmetricDecrypt::decrypt_ChaCha20;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test__CHA_CHA_20() throws Exception {
        EncryptOperation so = SymmetricEncrypt::encrypt_ChaCha20;
        DecryptOperation deo = SymmetricDecrypt::decrypt_ChaCha20;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, PROVIDER, PADDING, MODE);
    }

    // AES GCM
    @Test
@HunterDebug
    
    public void test_AES_GCM_NoPadding_AndroidKeyStore() throws Exception {
        String mode = "GCM";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_AES_GCM_NoPadding_AndroidOpenSSL() throws Exception {
        String mode = "GCM";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    // AES GCM - SIV

    @Test
@HunterDebug
    
    public void test_AES_GCM_siv_NoPadding_AndroidOpenSSL() throws Exception {
        String mode = "GCM-SIV";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    // CBC

    @Test
@HunterDebug
    
    public void test_AES_CBC_NoPadding_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_AES_CBC_PKCS7Padding_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS7PADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_AES_CBC_PKCS5Padding_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS5PADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    // ECB NO padding

    @Test
@HunterDebug
    
    public void test_AES_ECB_NOPADDING_AndroidOpenSSL() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_AES_ECB_NOPADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }


    @Test
@HunterDebug
    
    public void test_AES_ECB_PKCS5PADDING_AndroidOpenSSL() throws Exception {
        String mode = "ECB";
        String padd = "PKCS5PADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_AES_ECB_PKCS7PADDING_AndroidOpenSSL() throws Exception {
        String mode = "ECB";
        String padd = "PKCS7PADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    // CTR NO padding

    @Test
@HunterDebug
    
    public void test_AES_CTR_NOPADDING_AndroidOpenSSL() throws Exception {
        String mode = "CTR";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_AES_CTR_NOPADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "CTR";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }


    @Test
@HunterDebug
    
    public void test_AES() throws Exception {
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_AES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, PROVIDER, PADDING, MODE);
    }

    // DES - ECB

    @Test
@HunterDebug
    
    public void test_DES_ECB_NOPADDING_BC() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_DES_ECB_PKCS5PADDING_BC() throws Exception {
        String mode = "ECB";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_DES_ECB_PKCS7PADDING_BC() throws Exception {
        String mode = "ECB";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    // DES - CTR
    @Test
@HunterDebug
    
    public void test_DES_CTR_NOPADDING_BC() throws Exception {
        String mode = "CTR";
        String padd = "NOPADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_DES_CTR_PKCS5PADDING_BC() throws Exception {
        String mode = "CTR";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_DES_CTR_PKCS7PADDING_BC() throws Exception {
        String mode = "CTR";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    // DES - CBC

    @Test
@HunterDebug
    
    public void test_DES_CBC_NOPADDING_BC() throws Exception {
        String mode = "CBC";
        String padd = "NOPADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_DES_CBC_PKCS5PADDING_BC() throws Exception {
        String mode = "CBC";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_DES_CBC_PKCS7PADDING_BC() throws Exception {
        String mode = "CBC";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    // DES - OFB

    @Test
@HunterDebug
    
    public void test_DES_OFB_NOPADDING_BC() throws Exception {
        String mode = "OFB";
        String padd = "NOPADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_DES_OFB_PKCS5PADDING_BC() throws Exception {
        String mode = "OFB";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_DES_OFB_PKCS7PADDING_BC() throws Exception {
        String mode = "OFB";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }


    @Test
@HunterDebug
    
    public void test_3ES() throws Exception {
        EncryptOperation so = SymmetricEncrypt::encrypt_DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, PROVIDER, PADDING, MODE);
    }



    // 3DES (DESEDE) - CBC

    @Test
@HunterDebug
    
    public void test_3DES_CBC_NOPADDING_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_3DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_3DES_CBC_PKCS5PADDING_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS5PADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_3DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_3DES_CBC_PKCS7PADDING_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS7PADDING";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_3DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    // 3DES (DESEDE) - CBC

    @Test
@HunterDebug
    
    public void test_3DES_ECB_NOPADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        EncryptOperation so = SymmetricEncrypt::encrypt_3DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_3DES_ECB_PKCS7PADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "ECB";
        String padd = "PKCS7PADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        EncryptOperation so = SymmetricEncrypt::encrypt_3DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_3DES() throws Exception {
        EncryptOperation so = SymmetricEncrypt::encrypt_3DES;
        DecryptOperation deo = SymmetricDecrypt::decrypt_3DES;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, PROVIDER, PADDING, MODE);
    }

    // ARC4

    @Test
@HunterDebug
    
    public void test_ARC4_BC() throws Exception {
        String mode = "";
        String padd = "";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_ARC4;
        DecryptOperation deo = SymmetricDecrypt::decrypt_ARC4;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_ARC4_AndroidOpenSSL() throws Exception {
        String mode = "";
        String padd = "";
        String provider = "AndroidOpenSSL";
        EncryptOperation so = SymmetricEncrypt::encrypt_ARC4;
        DecryptOperation deo = SymmetricDecrypt::decrypt_ARC4;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }

    @Test
@HunterDebug
    
    public void test_ARC4() throws Exception {
        EncryptOperation so = SymmetricEncrypt::encrypt_ARC4;
        DecryptOperation deo = SymmetricDecrypt::decrypt_ARC4;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, PROVIDER, PADDING, MODE);
    }

    // BLOWFISH

    
    @Test
@HunterDebug
    public void test_BLOWFISH_BC() throws Exception {
        String mode = "";
        String padd = "";
        String provider = "BC";
        EncryptOperation so = SymmetricEncrypt::encrypt_BLOWFISH;
        DecryptOperation deo = SymmetricDecrypt::decrypt_BLOWFISH;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, provider, padd, mode);
    }


    
    @Test
@HunterDebug
    public void test_BLOWFISH() throws Exception {
        EncryptOperation so = SymmetricEncrypt::encrypt_BLOWFISH;
        DecryptOperation deo = SymmetricDecrypt::decrypt_BLOWFISH;
        encrypt_decrypt(so, deo, SECRET_KEY, INPUT_PARAMS, PROVIDER, PADDING, MODE);
    }

}
