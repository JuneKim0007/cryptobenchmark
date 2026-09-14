package com.example.cryptobenchmark.bench.fixture.workload;

import java.nio.ByteBuffer;
import java.security.SecureRandom;
import java.util.Random;
import static com.example.cryptobenchmark.crypto.codec.Codec.byteArrayToString;

import static com.example.cryptobenchmark.crypto.codec.Codec.byteArrayToStringBase64;
import static com.example.cryptobenchmark.crypto.codec.Codec.intToByteArray;

public class StringType implements DataType{


    private String value;

    public StringType() {
        this.value = "";
    }

    public StringType(String value) {
        this.value = value;
    }

    public static DataType genRandomWithSizeBase64(int size_bytes){
        SecureRandom rnd = new SecureRandom();
        byte[] token = new byte[size_bytes];
        rnd.nextBytes(token);
        return new StringType(byteArrayToStringBase64(token).substring(0, size_bytes));
        //System.out.println(token.length);
        //return new StringType(byteArrayToString(token));
    }

    public static DataType genPseudoRandomWithSizeBase64(int size_bytes, int seed){
        Random rnd =  new Random();
        rnd.setSeed(seed);
        byte[] token = new byte[size_bytes];
        rnd.nextBytes(token);
        return new StringType(byteArrayToStringBase64(token).substring(0, size_bytes));
    }


    public static DataType genRandomWithSize(int string_size){
        String characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        // Create a StringBuilder to store the random string
        StringBuilder stringBuilder = new StringBuilder();
        // Create a Random object to generate random indices
        Random random = new Random();
        // Generate random characters and append them to the StringBuilder until the desired length is reached
        for (int i = 0; i < string_size; i++) {
            int randomIndex = random.nextInt(characters.length()+ i);
            char randomChar = characters.charAt(randomIndex % characters.length());
            stringBuilder.append(randomChar);
        }
        return new StringType(stringBuilder.toString());
    }

    public static DataType genPseudoRandomWithSize(int string_size, int seed){
        String characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        // Create a StringBuilder to store the random string
        StringBuilder stringBuilder = new StringBuilder();
        // Create a Random object to generate random indices
        Random random = new Random(seed);
        // Generate random characters and append them to the StringBuilder until the desired length is reached
        for (int i = 0; i < string_size; i++) {
            int randomIndex = random.nextInt(characters.length()+ i);
            char randomChar = characters.charAt(randomIndex % characters.length());
            stringBuilder.append(randomChar);
        }

        return new StringType(stringBuilder.toString());
    }

    public static DataType[] genRandomWithSize(int size, int count){
        DataType[] x = new StringType[count];
        for (int i = 0; i < count; i++) {
            x[i] = genRandomWithSize(size);
        }
        return x;
    }

    public static DataType[] genPseudoRandomWithSize(int size, int seed, int count){
        DataType[] x = new StringType[count];
        int new_seed = seed;
        for (int i = 0; i < count; i++) {
            x[i] =  genPseudoRandomWithSize(size, new_seed);
            new_seed = new_seed + i;
        }
        return x;
    }

    @Override
    public Object getValue() {
        return value;
    }


    /*public static String[] genRandomStringsWithSize(int size, int count){
        String[] x = new String[count];
        for (int i = 0; i < count; i++) {
            x[i] = ((String) ((StringType) genRandomWithSize(size)).getValue());
        }
        return x;
    }*/
}
