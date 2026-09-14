package com.example.cryptobenchmark.environment.setup.config;

import android.os.Environment;
import android.util.Log;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

public class Config {

    public static String CONFIG_FILE = "CryptoBenchmark.config";

    public static Map<String,String> getConfigs(){
        Map<String,String> configs = new HashMap<>();
        File file = new File(Environment.getExternalStorageDirectory(), CONFIG_FILE);
        if (!file.exists()){
            Log.e("Config", "File not found: " + file.getAbsolutePath());
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
