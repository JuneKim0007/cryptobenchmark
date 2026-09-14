package com.example.cryptobenchmark;

import androidx.test.runner.AndroidJUnit4;

import com.example.cryptobenchmark.crypto.primitive.digest.Digest;
import com.example.cryptobenchmark.benchmark.preparation.workload.StringType;

import org.junit.Test;
import org.junit.runner.RunWith;


import static org.junit.Assert.*;

/**
 * Instrumented test, which will execute on an Android device.
 *
 * @see <a href="http://d.android.com/tools/testing">Testing documentation</a>
 */

@RunWith(AndroidJUnit4.class)
public class DataTypesTest {

    @Test
    public void testStringTypeRandomType() {
        assertTrue(StringType.genRandomWithSize(1) instanceof StringType);
        assertTrue(StringType.genRandomWithSize(2).getValue() instanceof String);
        assertTrue(StringType.genPseudoRandomWithSize(1, 1) instanceof StringType);
        assertTrue(StringType.genPseudoRandomWithSize(2, 2).getValue() instanceof String);
    }
    @Test
    public void testStringTypeRandomness() {
        String res_1 = (String) StringType.genRandomWithSize(64).getValue();
        String res_2 = (String) StringType.genRandomWithSize(64).getValue();
        assertNotEquals(res_1, res_2);
        res_1 = (String) StringType.genPseudoRandomWithSize(64, 1).getValue();
        res_2 = (String) StringType.genPseudoRandomWithSize(64, 2).getValue();
        assertNotEquals(res_1, res_2);
        res_1 = (String) StringType.genPseudoRandomWithSize(64, 1).getValue();
        res_2 = (String) StringType.genPseudoRandomWithSize(64, 1).getValue();
        assertEquals(res_1, res_2);
    }


    @Test
    public void testStringLength() {
        int size = 128;
        assertEquals(size, ((String) StringType.genRandomWithSize(size).getValue()).length());
        assertEquals(size, ((String) StringType.genPseudoRandomWithSize(size, size).getValue()).length());
    }
}