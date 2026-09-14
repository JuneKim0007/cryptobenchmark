package com.example.cryptobenchmark.crypto.codec;

import java.io.UnsupportedEncodingException;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

public class Codec {

    public static String standardCharSet = StandardCharsets.UTF_8.toString();

    public static String byteArrayToString(byte[] cyphertext){
        try{
            return new String(cyphertext, standardCharSet);
        }
        catch (UnsupportedEncodingException e){
            e.printStackTrace();
        }
        return new String(cyphertext);
    }

    public static byte[] StringToByteArray(String cyphertext){
        try{
            return cyphertext.getBytes(standardCharSet);
        }
        catch (UnsupportedEncodingException e){
            e.printStackTrace();
        }
        return cyphertext.getBytes();
    }

    public static String byteArrayToStringBase64(byte[] cyphertext){
        return Base64.getEncoder().encodeToString(cyphertext);
    }

    public static byte[] StringToByteArrayBase64(String cyphertext){
        return Base64.getDecoder().decode(cyphertext);
    }

    public static byte[] intToByteArray(int data) {
        byte[] result = new byte[4];
        result[0] = (byte) ((data & 0xFF000000) >> 24);
        result[1] = (byte) ((data & 0x00FF0000) >> 16);
        result[2] = (byte) ((data & 0x0000FF00) >> 8);
        result[3] = (byte) ((data & 0x000000FF) >> 0);
        return result;
    }
}
