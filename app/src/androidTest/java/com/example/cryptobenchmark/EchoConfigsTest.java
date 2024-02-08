package com.example.cryptobenchmark;

import androidx.test.runner.AndroidJUnit4;
import android.util.Log;
import com.example.cryptobenchmark.digest.Digest;
import com.example.cryptobenchmark.digest.DigestOperation;
import com.example.cryptobenchmark.misc.DeviceCryptoPrimitives;
import com.example.cryptobenchmark.misc.datatypes.StringType;
import com.hunter.library.debug.HunterDebug;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

/**
 * Instrumented test, which will execute on an Android device.
 *
 * @see <a href="http://d.android.com/tools/testing">Testing documentation</a>
 */
@RunWith(AndroidJUnit4.class)
public class EchoConfigsTest extends MeasureTest{


    @Test
    @HunterDebug
    public void test_echo_cfgs(){
        Log.d("EchoConfigsTest", "inputSize: " + inputSize);
        Log.d("EchoConfigsTest", "keyLen: " + keyLen);
        Log.d("EchoConfigsTest", "nTimes: " + nTimes);
        Log.d("EchoConfigsTest", "warmup_time: " + warmup_time);
        Log.d("EchoConfigsTest", "cool_down_time: " + cool_down_time);
        Log.d("EchoConfigsTest", "PROVIDER: " + PROVIDER);
        Log.d("EchoConfigsTest", "ALGORITHM: " + ALGORITHM);
        Log.d("EchoConfigsTest", "MODE: " + MODE);
        Log.d("EchoConfigsTest", "PADDING: " + PADDING);
        Log.d("EchoConfigsTest", "WITH_KEY_SPEC: " + WITH_KEY_SPEC);
    }

}