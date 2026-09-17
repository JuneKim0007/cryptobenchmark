package io.github.junekim0007.cryptobench.crypto.codec;

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
}
