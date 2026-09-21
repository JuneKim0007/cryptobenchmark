package io.github.junekim0007.cryptobench;

import androidx.test.runner.AndroidJUnit4;

import io.github.junekim0007.cryptobench.crypto.primitive.digest.Digest;
import io.github.junekim0007.cryptobench.preparation.workload.DataType;
import io.github.junekim0007.cryptobench.preparation.workload.StringType;
import com.hunter.library.debug.HunterDebug;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;


/**
 * Instrumented test, which will execute on an Android device.
 *
 * @see <a href="http://d.android.com/tools/testing">Testing documentation</a>
 */
@RunWith(AndroidJUnit4.class)
public class DigestTest {

    public static int inputSize = Integer.parseInt(BuildConfig.INPUT_SIZE);
    public static int nTimes = Integer.parseInt(BuildConfig.N_TIMES);
    public static int warmup_time = Integer.parseInt(BuildConfig.WARM_UP_TIME);
    public static int cool_down_time = Integer.parseInt(BuildConfig.COOL_DOWN_TIME);
    public static String provider =BuildConfig.PROVIDER;
    public static String[] inputs =  gen_random_workload(inputSize, nTimes);

    @Before
    public void before_tests(){
        try {
            System.out.println("before");
            Thread.sleep(warmup_time);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    @After
    public void after_tests(){
        try {
            System.out.println("after");
            Thread.sleep(cool_down_time);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public static String[] gen_random_workload(int size, int times){
        String[] res = new String[times];
        DataType[] dt = StringType.genRandomWithSize(size, times);
        for (int i = 0; i < dt.length; i++) {
            res[i] = ((String) dt[i].getValue());
        }
        return res;
    }

   public void execute_digest_algorithm(String algorithm, String[] params, String provider){
        for (int i = 0; i < params.length ; i++) {
            //String target = i > params.length-1 ? params[i % (params.length)] : params[i];
            Digest.digest( params[i], algorithm, provider);
        }
    }

    
    @Test
    public void test_md5(){
        execute_digest_algorithm("MD5", inputs, provider);
    }

    
    @Test
    public void test_sha1(){
        execute_digest_algorithm("SHA1", inputs, provider);
    }

    
    @Test
    public void test_sha224(){
        execute_digest_algorithm("SHA224", inputs, provider);
    }

    
    @Test
    public void test_sha256(){
        execute_digest_algorithm("SHA256", inputs, provider);
    }

    @Test
    
    public void test_sha384(){
        execute_digest_algorithm("SHA384", inputs, provider);
    }

    
    @Test
    public void test_sha512(){
        execute_digest_algorithm("SHA512", inputs, provider);
    }

}