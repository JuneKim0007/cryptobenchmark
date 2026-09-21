package io.github.junekim0007.cryptobench;

import io.github.junekim0007.cryptobench.preparation.workload.StringType;

import org.junit.Test;

import static org.junit.Assert.*;
import static io.github.junekim0007.cryptobench.crypto.codec.Codec.StringToByteArray;
import static io.github.junekim0007.cryptobench.crypto.codec.Codec.byteArrayToString;

public class LocalDataTypesTest {

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
    public void testStringEquals() {
        String res_1 = (String) StringType.genRandomWithSize(64).getValue();
        String res_2 = byteArrayToString(StringToByteArray(res_1));
        assertEquals(res_1, res_2);
        res_1 = (String) StringType.genPseudoRandomWithSize(64, 1).getValue();
        res_2  = byteArrayToString(StringToByteArray(res_1));
        assertEquals(res_1, res_2);
        res_1 = (String) StringType.genPseudoRandomWithSize(128, 1).getValue();
        res_2 =  byteArrayToString(StringToByteArray(res_1));
        assertEquals(res_1, res_2);

    }
}

