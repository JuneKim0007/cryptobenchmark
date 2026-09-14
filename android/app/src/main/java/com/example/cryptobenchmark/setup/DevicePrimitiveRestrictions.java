package com.example.cryptobenchmark.setup;

import android.content.Context;

import com.example.cryptobenchmark.R;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.InputStream;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Scanner;
import java.util.Set;

public class DevicePrimitiveRestrictions {

    public static final String DEFAULT_PATH =  "src/main/res/raw/known_primitive_restrictions.json";
    private String deviceName;
    private JSONObject inclusions = new JSONObject();
    private JSONObject exclusions = new JSONObject();


    public DevicePrimitiveRestrictions() {
        this.deviceName = "unknown";
        this.inclusions = new JSONObject();
        this.exclusions = new JSONObject();
    }

    public DevicePrimitiveRestrictions(Context ctx) {
        JSONObject jo = this.loadSONFile(ctx);
        try {
            this.loadFromJSONObject(jo);
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    public DevicePrimitiveRestrictions(String filepath) {
        this.deviceName = "Unknown";
        try {
            this.loadFromJSONObject(filepathToJSON(filepath));
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    public DevicePrimitiveRestrictions(String deviceName, Map<String, CryptoProvider> deviceProviders) {
        this.deviceName = deviceName;
    }

    public String getDeviceName() {
        return deviceName;
    }

    private JSONObject filepathToJSON(String filepath){
        try {
            return new JSONObject(readStream(new FileInputStream(filepath)));
        } catch (FileNotFoundException | JSONException e) {
            e.printStackTrace();
        }
        return null;
    }

    private JSONObject loadSONFile(Context ctx){
        String filecontent = null;
        JSONObject jo = new JSONObject();
        try {
            filecontent = readStream(ctx.getResources().openRawResource(R.raw.restrictions));
        } catch (Exception e) {
            e.printStackTrace();
        }
        try {
            return new JSONObject(filecontent);
        } catch (JSONException e) {
            e.printStackTrace();
        }
        return jo;
    }

    public void loadFromJSONObject(JSONObject jo) throws JSONException {
        if (jo!=null) {
            this.deviceName = jo.has("device") ? jo.getString("device") : this.deviceName;
            this.inclusions = jo.has("include") ? jo.getJSONObject("include") : new JSONObject();
            this.exclusions = jo.has("exclude") ? jo.getJSONObject("exclude") : new JSONObject();
        }
    }

    private String readStream(InputStream is) {
        Scanner s = new Scanner(is).useDelimiter("\\A");
        return s.hasNext() ? s.next() : "";
    }

    public Map<String, CryptoProvider> filterPrimitives( Map<String, CryptoProvider> deviceProviders) throws JSONException {
        // exclusions
        Map<String, Set<String>> excludes = new HashMap<>();
        if (this.exclusions.length()>0){
            for (Iterator<String> it = this.exclusions.getJSONObject("algos").keys(); it.hasNext(); ) {
                String algorithm = it.next();
                for (CryptoProvider candCp : deviceProviders.values()){
                    for (CryptoPrimitive x : candCp.getProviderPrimitives().values()) {
                        if (x.getPrimitiveName().equals(algorithm)) {
                            JSONArray providersToExclude = this.exclusions.getJSONObject("algos").getJSONObject(algorithm).getJSONArray("providers");
                            if(providersToExclude.length() > 0 && (providersToExclude.get(0).equals("all") || candCp.equals(providersToExclude))){
                                // exclude cypher on this provider
                                Object o = excludes.containsKey(candCp.getProviderName()) ? excludes.get(candCp.getProviderName()).add(algorithm) : excludes.put(candCp.getProviderName(), new HashSet<>(Arrays.asList(algorithm)));
                            }
                        }
                    }
                }
            }
            // exclude algos
            excludes.keySet().stream().forEach( t ->  excludes.keySet().stream().forEach( et -> excludes.get(et).forEach(x -> deviceProviders.get(et).removePrimitive(x))));
            // exclude providers
            for (int i = 0; i < this.exclusions.getJSONArray("providers").length() ; i++) {
                deviceProviders.remove(this.exclusions.getJSONArray("providers").get(i));
            }
        }

        if (this.inclusions.length()>0){
            // inclusions (including restrictions)
            for (Iterator<String> it = this.inclusions.getJSONObject("algos").keys(); it.hasNext(); ) {
                String algorithm = it.next();
                for (CryptoProvider candCp : deviceProviders.values()){
                    if(candCp.getProviderPrimitives().containsKey(algorithm)){
                        System.out.println();
                        CryptoPrimitive cp = candCp.getProviderPrimitives().get(algorithm);
                        for (Iterator<String> it2 = this.inclusions.getJSONObject("algos").getJSONObject(algorithm).keys(); it2.hasNext();){
                            String key = it2.next();
                            if (key.equals("key_sizes")){
                                if(cp instanceof ConfigurableCryptoPrimitive){
                                    JSONArray jas = this.inclusions.getJSONObject("algos").getJSONObject(algorithm).getJSONArray("key_sizes");
                                    for (int i = 0; i < jas.length() ; i++) {
                                        ((ConfigurableCryptoPrimitive) cp).addKeyLen(jas.getInt(i));
                                    }
                                }
                                else{
                                    System.out.println("erro. transformar em configurable");
                                }
                            }
                        }

                    }
                }
            }
        }
        return deviceProviders;
    }
}
