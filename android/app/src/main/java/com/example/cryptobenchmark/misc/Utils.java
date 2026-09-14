package com.example.cryptobenchmark.misc;




import android.app.Application;
import android.content.Context;

import org.json.JSONObject;

import java.util.Map;
import java.util.HashMap;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.UnsupportedEncodingException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.Provider;
import java.security.Security;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Set;
import android.util.Log;
import android.os.Environment;
import java.io.BufferedReader;
import java.nio.charset.StandardCharsets;
import com.example.cryptobenchmark.misc.datatypes.StringType;


public class Utils {

    public static String CONFIG_FILE = "CryptoBenchmark.config";


    private static final void showHashAlgorithms(Provider prov, Class<?> typeClass) {
        String type = typeClass.getSimpleName();
        List<Provider.Service> algos = new ArrayList<>();
        Set<Provider.Service> services = prov.getServices();
        for (Provider.Service service : services) {
            if (service.getType().equalsIgnoreCase(type)) {
                algos.add(service);
            }
        }

        if (!algos.isEmpty()) {
            System.out.printf(" --- Provider %s, version %.2f --- %n", prov.getName(), prov.getVersion());
            for (Provider.Service service : algos) {
                String algo = service.getAlgorithm();
                System.out.printf("Algorithm name: \"%s\"%n", algo);
            }
        }

        // --- find aliases (inefficiently)
        Set<Object> keys = prov.keySet();
        for (Object key : keys) {
            final String prefix = "Alg.Alias." + type + ".";
            if (key.toString().startsWith(prefix)) {
                String value = prov.get(key.toString()).toString();
                System.out.printf("Alias: \"%s\" -> \"%s\"%n",
                        key.toString().substring(prefix.length()),
                        value);
            }
        }
    }

    public static void listHashAlgorithms() {
        Provider[] providers = Security.getProviders();
        for (Provider provider : providers) {
            showHashAlgorithms(provider, MessageDigest.class);
        }
    }

    public static String byteArrayToString(byte[] cyphertext){
        // return Base64.getUrlEncoder().withoutPadding().encodeToString(cyphertext);
        try{
            return new String(cyphertext, StringType.standardCharSet);
        }
        catch (UnsupportedEncodingException e){
            e.printStackTrace();
        }
        return new String(cyphertext);
    }

    public static byte[] StringToByteArray(String cyphertext){
        try{
            return cyphertext.getBytes(StringType.standardCharSet);
        }
        catch (UnsupportedEncodingException e){
            e.printStackTrace();
        }
        return cyphertext.getBytes(); //Base64.getDecoder().decode(cyphertext);
    }

    public static String byteArrayToStringBase64(byte[] cyphertext){
        // return Base64.getUrlEncoder().withoutPadding().encodeToString(cyphertext);
        return Base64.getEncoder().encodeToString(cyphertext);
    }

    public static byte[] StringToByteArrayBase64(String cyphertext){
        return Base64.getDecoder().decode(cyphertext);
    }




    public static Method getMethod(String cname, String mname, Class[] parameterTypes){
        Class<?> c = null;
        try {
            c = Class.forName(cname);
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
        Method method = null;
        try {
            method = c.getDeclaredMethod( mname, parameterTypes);
        } catch (NoSuchMethodException e) {
            e.printStackTrace();
        }
        return method;
    }

    public static byte[] intToByteArray(int data) {
        byte[] result = new byte[4];
        result[0] = (byte) ((data & 0xFF000000) >> 24);
        result[1] = (byte) ((data & 0x00FF0000) >> 16);
        result[2] = (byte) ((data & 0x0000FF00) >> 8);
        result[3] = (byte) ((data & 0x000000FF) >> 0);
        return result;
    }

    private static Application getApplicationUsingReflection() throws Exception {
        return (Application) Class.forName("android.app.ActivityThread")
                .getMethod("currentApplication").invoke(null, (Object[]) null);
    }

    public JSONObject loadJSONFromFile(String filename) {
        return new JSONObject();
    }

    public static Map<String,String> getConfigs(){
        Map<String,String> configs = new HashMap<>();
        File file = new File(Environment.getExternalStorageDirectory(), CONFIG_FILE);
        if (!file.exists()){
            Log.e("Utils", "File not found: " + file.getAbsolutePath());
            return configs;
        }
        try {
            BufferedReader bufferedReader = new BufferedReader(new FileReader(file));
            String line;
            while ((line = bufferedReader.readLine()) != null) {
                if (line.contains("=")){
                    String[] parts = line.split("=");
                    if (parts.length >= 2){
                        configs.put(parts[0].toUpperCase(), parts[1]);
                    }
                }
            }
            bufferedReader.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return configs;
    }

}
