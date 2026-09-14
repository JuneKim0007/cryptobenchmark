package com.example.cryptobenchmark.misc.datatypes;

public interface DataType {

    public static DataType genRandomWithSize(int size){ return null; }

    public static DataType genPseudoRandomWithSize(int size, int seed){
        return null;
    }

    public static DataType[] genRandomWithSize(int size, int count){ return null; }

    public static DataType[] genPseudoRandomWithSize(int size, int seed, int count){
        return null;
    }

    public Object getValue();


}
