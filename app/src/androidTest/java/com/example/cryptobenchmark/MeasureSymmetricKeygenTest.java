package com.example.cryptobenchmark;

import androidx.test.runner.AndroidJUnit4;
import com.example.cryptobenchmark.encrypt.symmetric.SymmetricEncrypt;
import com.example.cryptobenchmark.encrypt.symmetric.EncryptOperation;
import com.hunter.library.debug.HunterDebug;
import org.junit.Test;
import org.junit.runner.RunWith;
import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;

import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_ARC4;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_AES;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_AES_AndroidKeyStore;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_BLOWFISH;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_ChaCha20;
import static com.example.cryptobenchmark.keygen.symmetric.SymmetricKeyGen.gen_key_DES;

@RunWith(AndroidJUnit4.class)
public class MeasureSymmetricKeygenTest extends MeasureTest {

    // CHACHA20

    public static void gen_cha_cha(int keylen, String provider) throws Exception {
        for (int i = 0; i < INPUT_MESSAGES.length; i++) {
            gen_key_ChaCha20(keylen, provider);
        }
    }

    @Test
    @HunterDebug
    public void test_key_gen_CHA_CHA_20_AndroidOpenSSL() throws Exception {
        String algo = "ChaCha20";
        String provider = "AndroidOpenSSL";
        gen_cha_cha(keyLen, provider);
    }

    // CHACHA20

    @Test
    @HunterDebug
    public void test_key_gen_CHA_CHA_20() throws Exception {
        gen_cha_cha(keyLen, PROVIDER);
    }

   /*

    @Test
@HunterDebug
    public void test_aes_solo() throws Exception {
        String provider = "AndroidOpenSSL";
        String padd = "";
        String mode = "";
        SecretKey sk = gen_key_AES(keyLen, mode, padd);
        EncryptOperation so = SymmetricEncrypt::encrypt_AES;
        so.encrypt(INPUT_PARAMS[0], "", "", sk, "");
    }*/


    public static void gen_aes(int keylen, String mode, String padd, String provider) throws Exception {
        for (int i = 0; i < INPUT_MESSAGES.length; i++) {
            gen_key_AES(keylen, mode, padd, provider);
        }
    }

    // AES GCM
    @Test
    @HunterDebug
    public void test_key_gen_AES_GCM_NoPadding_AndroidKeyStore() throws Exception {
        String mode = "GCM";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        gen_aes(keyLen, mode, padd, provider);;
    }

    @Test
    @HunterDebug

    public void test_key_gen_AES_GCM_NoPadding_AndroidOpenSSL() throws Exception {
        String mode = "GCM";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        gen_aes(keyLen, mode, padd, provider);;
    }

    @Test
    @HunterDebug

    public void test_key_gen_AES_GCM_NoPadding() throws Exception {
        String mode = "GCM";
        String padd = "NOPADDING";
        gen_aes(keyLen, mode, padd, PROVIDER);;
    }

    // AES GCM - SIV

    @Test
    @HunterDebug

    public void test_key_gen_AES_GCM_siv_NoPadding_AndroidOpenSSL() throws Exception {
        String mode = "GCM-SIV";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        gen_aes(keyLen, mode, padd, provider);;
    }

    @Test
    @HunterDebug
    public void test_key_gen_AES_GCM_siv_NoPadding() throws Exception {
        String mode = "GCM-SIV";
        String padd = "NOPADDING";
        gen_aes(keyLen, mode, padd, PROVIDER);
    }

    // CBC

    @Test
    @HunterDebug
    public void test_key_gen_AES_CBC_NoPadding_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        gen_aes(keyLen, mode, padd, provider);;
    }

    @Test
    @HunterDebug

    public void test_key_gen_AES_CBC_PKCS7Padding_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS7PADDING";
        String provider = "AndroidOpenSSL";
        gen_aes(keyLen, mode, padd, provider);;
    }

    @Test
    @HunterDebug

    public void test_key_gen_AES_CBC_PKCS5Padding_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS5PADDING";
        String provider = "AndroidOpenSSL";
        gen_aes(keyLen, mode, padd, provider);;
    }

    @Test
    @HunterDebug

    public void test_key_gen_AES_ECB_NOPADDING_AndroidOpenSSL() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        gen_aes(keyLen, mode, padd, provider);;
    }

    @Test
    @HunterDebug

    public void test_key_gen_AES_ECB_NOPADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        gen_aes(keyLen, mode, padd, provider);;
    }


    @Test
    @HunterDebug
    public void test_key_gen_AES_ECB_PKCS5PADDING_AndroidOpenSSL() throws Exception {
        String mode = "ECB";
        String padd = "PKCS5PADDING";
        String provider = "AndroidOpenSSL";
        gen_aes(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug

    public void test_key_gen_AES_ECB_PKCS7PADDING_AndroidOpenSSL() throws Exception {
        String mode = "ECB";
        String padd = "PKCS7PADDING";
        String provider = "AndroidOpenSSL";
        gen_aes(keyLen, mode, padd, provider);
    }

    // CTR NO padding

    @Test
    @HunterDebug
    public void test_key_gen_AES_CTR_NOPADDING_AndroidOpenSSL() throws Exception {
        String mode = "CTR";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        gen_aes(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug
    public void test_key_gen_AES_CTR_NOPADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "CTR";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        gen_aes(keyLen, mode, padd, provider);
    }


    @Test
    @HunterDebug
    public void test_key_gen_AES_ANY() throws Exception {
        gen_aes(keyLen, MODE, PADDING, PROVIDER);
    }



    public static void gen_des(int keylen, String mode, String padding, String provider) throws Exception {
        for (int i = 0; i < INPUT_MESSAGES.length; i++) {
            gen_key_DES(keyLen, mode, padding, provider);
        }
    }


    // DES - ECB

    @Test
    @HunterDebug
    public void test_key_gen_DES_ECB_NOPADDING_BC() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug

    public void test_key_gen_DES_ECB_PKCS5PADDING_BC() throws Exception {
        String mode = "ECB";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug

    public void test_key_gen_DES_ECB_PKCS7PADDING_BC() throws Exception {
        String mode = "ECB";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    // DES - CTR
    @Test
    @HunterDebug
    public void test_key_gen_DES_CTR_NOPADDING_BC() throws Exception {
        String mode = "CTR";
        String padd = "NOPADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug

    public void test_key_gen_DES_CTR_PKCS5PADDING_BC() throws Exception {
        String mode = "CTR";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug
    public void test_key_gen_DES_CTR_PKCS7PADDING_BC() throws Exception {
        String mode = "CTR";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    // DES - CBC

    @Test
    @HunterDebug
    public void test_key_gen_DES_CBC_NOPADDING_BC() throws Exception {
        String mode = "CBC";
        String padd = "NOPADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug
    public void test_key_gen_DES_CBC_PKCS5PADDING_BC() throws Exception {
        String mode = "CBC";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug
    public void test_key_gen_DES_CBC_PKCS7PADDING_BC() throws Exception {
        String mode = "CBC";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    // DES - OFB

    @Test
    @HunterDebug
    public void test_key_gen_DES_OFB_NOPADDING_BC() throws Exception {
        String mode = "OFB";
        String padd = "NOPADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug
    public void test_key_gen_DES_OFB_PKCS5PADDING_BC() throws Exception {
        String mode = "OFB";
        String padd = "PKCS5PADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug
    public void test_key_gen_DES_OFB_PKCS7PADDING_BC() throws Exception {
        String mode = "OFB";
        String padd = "PKCS7PADDING";
        String provider = "BC";
        gen_des(keyLen, mode, padd, provider);
    }


    @Test
    @HunterDebug
    public void test_key_gen_DES_ANY() throws Exception {
        gen_des(keyLen, MODE, PADDING, PROVIDER);

    }


    // 3DES (DESEDE) - CBC

    @Test
    @HunterDebug

    public void test_key_gen_3DES_CBC_NOPADDING_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "NOPADDING";
        String provider = "AndroidOpenSSL";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug

    public void test_key_gen_DES_CBC_PKCS5PADDING_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS5PADDING";
        String provider = "AndroidOpenSSL";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug

    public void test_key_gen_3DES_CBC_PKCS7PADDING_AndroidOpenSSL() throws Exception {
        String mode = "CBC";
        String padd = "PKCS7PADDING";
        String provider = "AndroidOpenSSL";
        gen_des(keyLen, mode, padd, provider);
    }

    // 3DES (DESEDE) - CBC

    @Test
    @HunterDebug

    public void test_key_gen_3DES_ECB_NOPADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "ECB";
        String padd = "NOPADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        gen_des(keyLen, mode, padd, provider);
    }

    @Test
    @HunterDebug

    public void test_key_gen_3DES_ECB_PKCS7PADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String mode = "ECB";
        String padd = "PKCS7PADDING";
        String provider = "AndroidKeyStoreBCWorkaround";
        gen_des(keyLen, mode, padd, provider);
    }


    @Test
    @HunterDebug

    public void test_key_gen_3DES_ANY() throws Exception {
        gen_des(keyLen, MODE, PADDING, PROVIDER);
    }


    // ARC4

    public static void gen_arc4(int keylen, String provider) throws Exception {
        for (int i = 0; i < INPUT_MESSAGES.length; i++) {
            gen_key_ARC4(keylen, provider);
        }
    }

    @Test
    @HunterDebug

    public void test_key_gen_ARC4_BC() throws Exception {
        String mode = "";
        String padd = "";
        String provider = "BC";
        gen_key_ARC4(keyLen, provider);
    }

    @Test
    @HunterDebug

    public void test_key_gen_ARC4_AndroidOpenSSL() throws Exception {
        String mode = "";
        String padd = "";
        String provider = "AndroidOpenSSL";
        gen_key_ARC4(keyLen, provider);
    }

    @Test
    @HunterDebug

    public void test_key_gen_ARC4_ANY() throws Exception {
        gen_key_ARC4(keyLen, PROVIDER);
    }


    // BLOWFISH

    public void gen_blowfish(int keylen, String provider) throws Exception {
        gen_key_BLOWFISH(keylen, provider);
    }


    @Test
    @HunterDebug
    public void test_key_gen_BLOWFISH_BC() throws Exception {
        String mode = "";
        String padd = "";
        String provider = "BC";
        gen_blowfish(keyLen, provider);
    }

    @Test
    @HunterDebug

    public void test_key_gen_BLOWFISH_ANY() throws Exception {
        gen_blowfish(keyLen, PROVIDER);
    }

}
