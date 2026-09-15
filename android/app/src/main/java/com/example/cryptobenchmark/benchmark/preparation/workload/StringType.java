package com.example.cryptobenchmark.benchmark.preparation.workload;

import java.util.Random;


public class StringType implements DataType{

    private String value;

    public StringType() {
        this.value = "";
    }

    public StringType(String value) {
        this.value = value;
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
