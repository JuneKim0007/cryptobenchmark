package io.github.junekim0007.cryptobench;

import org.junit.Test;
import java.security.KeyPair;
import io.github.junekim0007.cryptobench.crypto.primitive.cipher.asymmetric.AssymmetricEncryptKeyGen;
import com.hunter.library.debug.HunterDebug;

public class MeasureAssymmetricKeygenTest extends MeasureTest {

    public static void gen_key_pair_rsa(int keyLen, String provider,
                                       String mode, String padding, boolean withKeySpec){
        try {
            if (provider.toLowerCase().contains("androidkeystore")){
                if (withKeySpec){
                    for (int i = 0; i < INPUT_MESSAGES.length; i++) {
                        AssymmetricEncryptKeyGen.gen_key_rsakeyspec(keyLen, mode,
                                padding, provider);
                    }
                }
                else{
                    for (int i = 0; i < INPUT_MESSAGES.length; i++) {
                        AssymmetricEncryptKeyGen.gen_key_RSA(keyLen, mode, padding);
                    }
                }
            }
            else {
                for (int i = 0; i < INPUT_MESSAGES.length; i++) {
                    AssymmetricEncryptKeyGen.gen_key_RSA(keyLen);
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Test
    @HunterDebug
    public void test_RSA_ECB_PKCS1PADDING_AndroidOpenSSL() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "PKCS1PADDING";
        gen_key_pair_rsa(keyLen, "AndroidOpenSSL", mode, padding, false );

    }

    @Test
    @HunterDebug

    public void test_RSA_ECB_OAEPPADDING_AndroidOpenSSL() throws Exception{
        String algo = "RSA", mode = "ECB", padding = "OAEPPADDING";
        gen_key_pair_rsa(keyLen, "AndroidOpenSSL", mode, padding, false);
    }

    @Test
    @HunterDebug

    public void test_RSA_ECB_OAEPWITHSHA_1ANDMGF1PADDING_AndroidOpenSSL() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-1ANDMGF1PADDING";
        gen_key_pair_rsa(keyLen, "AndroidOpenSSL", mode, padding, false );
    }

    @Test
    @HunterDebug

    public void test_RSA_ECB_OAEPWITHSHA_224ANDMGF1PADDING_AndroidOpenSSL() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-224ANDMGF1PADDING";
        gen_key_pair_rsa(keyLen, "AndroidOpenSSL", mode, padding, false );
    }
    @Test
    @HunterDebug

    public void test_RSA_ECB_OAEPWITHSHA_256ANDMGF1PADDING_AndroidOpenSSL() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-256ANDMGF1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        gen_key_pair_rsa(keyLen, "AndroidOpenSSL", mode, padding, false );
    }

    @Test
    @HunterDebug

    public void test_RSA_ECB_OAEPWITHSHA_384ANDMGF1PADDING_AndroidOpenSSL() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-384ANDMGF1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        gen_key_pair_rsa(keyLen, "AndroidOpenSSL", mode, padding, false );
    }

    @Test
    @HunterDebug

    public void test_RSA_ECB_OAEPWITHSHA_512ANDMGF1PADDING_AndroidOpenSSL() throws Exception{
        // cannot be used with large block sizes (> 64?)
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-512ANDMGF1PADDING";
        //KeyPair kp = AssymmetricEncryptKeyGen.gen_key_RSA_AndroidKeyStore(512);
        gen_key_pair_rsa(keyLen, "AndroidOpenSSL", mode, padding, false );
    }

    @Test
    @HunterDebug

    public void test_RSA_ECB_PKCS1PADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "PKCS1PADDING", provider = "AndroidKeyStoreBCWorkaround";
        gen_key_pair_rsa(keyLen, provider, mode, padding, false );
    }

    @Test
    @HunterDebug

    public void test_RSA_ECB_OAEPPADDING_AndroidKeyStoreBCWorkaround() throws Exception{
        String algo = "RSA", mode = "ECB", padding = "PKCS1PADDING", provider = "AndroidKeyStoreBCWorkaround";
        gen_key_pair_rsa(keyLen, provider, mode, padding, false );
        // OK
    }

    @Test
    @HunterDebug

    public void test_RSA_ECB_OAEPWITHSHA_1ANDMGF1PADDING_AndroidKeyStoreBCWorkaround() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-1ANDMGF1PADDING",
                provider = "AndroidKeyStoreBCWorkaround";
        gen_key_pair_rsa(keyLen, provider, mode, padding, false);
    }

    @Test
    @HunterDebug

    public void test_RSA_ECB_OAEPWITHSHA_224ANDMGF1PADDING() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-224ANDMGF1PADDING";
        gen_key_pair_rsa(keyLen, PROVIDER, mode, padding, WITH_KEY_SPEC);
    }

    @Test
    @HunterDebug
    public void test_RSA_ECB_OAEPWITHSHA_256ANDMGF1PADDING() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-256ANDMGF1PADDING";
        gen_key_pair_rsa(keyLen, PROVIDER, mode, padding, true);
        // Only RSAKeyGenParameterSpec supported
    }

    @Test
    @HunterDebug
    public void test_RSA_ECB_OAEPWITHSHA_384ANDMGF1PADDING() throws Exception {
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-384ANDMGF1PADDING";
        gen_key_pair_rsa(keyLen, PROVIDER, mode, padding, WITH_KEY_SPEC );
    }

    @Test
    @HunterDebug
    public void test_RSA_ECB_OAEPWITHSHA_512ANDMGF1PADDING() throws Exception{
        // cannot be used with large block sizes (> 64?)
        String algo = "RSA", mode = "ECB", padding = "OAEPWITHSHA-512ANDMGF1PADDING";
        gen_key_pair_rsa(keyLen, PROVIDER, mode, padding, WITH_KEY_SPEC );
    }

}
