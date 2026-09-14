package com.example.cryptobenchmark.setup;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Optional;

public class CryptoProvider{

    private String providerName;
    private Map<String, CryptoPrimitive> providerPrimitives = new HashMap<>();

    public CryptoProvider(String providerName) {
        this.providerName = providerName;
    }

    public CryptoProvider(Map<String, CryptoPrimitive> providerPrimitives) {
        this.providerPrimitives = providerPrimitives;
    }

    public CryptoProvider(String providerName, Map<String, CryptoPrimitive> providerPrimitives) {
        this.providerName = providerName;
        this.providerPrimitives = providerPrimitives;
    }

    public String getProviderName() {
        return providerName;
    }

    public Map<String, CryptoPrimitive> getProviderPrimitives() {
        return providerPrimitives;
    }

    public void addPrimitive(String id , CryptoPrimitive cp) {
       this.providerPrimitives.put(id, cp);
    }

    public void removePrimitive(String primitiveName) {
        this.providerPrimitives.remove(primitiveName);
    }


    public CryptoPrimitive getFirstImplementedPrimitive(String primitiveName){
        Optional<CryptoPrimitive> opt = this.getProviderPrimitives().values().stream().filter(x-> x.getPrimitiveName().startsWith(primitiveName)).findAny();
        return opt.orElse(null);
    }


    public void loadFromJsonObject(JSONObject jo) throws JSONException {
        for (Iterator<String> it = jo.getJSONObject("algorithms").keys(); it.hasNext(); ) {
            String pmname = it.next();
            JSONObject algo = jo.getJSONObject("algorithms").getJSONObject(pmname);
            String simpleName = algo.has("simple_name") ? algo.getString("simple_name") : pmname;
            CryptoPrimitive cp = algo.length() == 0 ? new CryptoPrimitive(pmname, simpleName) : new ConfigurableCryptoPrimitive(pmname, simpleName);
            cp.loadFromJsonObject(algo);
            this.addPrimitive(pmname, cp);
        }
    }


}
