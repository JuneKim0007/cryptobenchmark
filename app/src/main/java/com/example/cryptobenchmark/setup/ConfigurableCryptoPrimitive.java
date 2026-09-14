package com.example.cryptobenchmark.setup;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

public class ConfigurableCryptoPrimitive extends CryptoPrimitive{

    private Map<String, CryptoParam> params = new HashMap<>();
    private Set<Integer> keylens = new HashSet<>();

    public ConfigurableCryptoPrimitive(String name) {
        super(name);
    }

    public ConfigurableCryptoPrimitive(String primitiveName, PrimitiveType primitiveType) {
        super(primitiveName, primitiveType);
    }

    public ConfigurableCryptoPrimitive(String primitiveName, String simpleName){
        super(primitiveName, simpleName);
    }

    public void addPrimitive(String id, CryptoParam cp){
        this.params.put(id, cp);
    }

    public CryptoParam getParam(String id){
        return this.params.get(id);
    }

    public Collection<CryptoParam> getParams(){
        return this.params.values();
    }

    public void addKeyLen(int keylen){
        this.keylens.add(keylen);
    }

    public void loadFromJsonObject(JSONObject jo) throws JSONException {
        if (jo.has("key_sizes")){
            JSONArray algo_keys = jo.getJSONArray("key_sizes");
            for (int i = 0; i < algo_keys.length() ; i++) {
                try {
                    Integer.parseInt(algo_keys.get(i).toString());
                    this.addKeyLen(algo_keys.getInt(i));
                }catch (NumberFormatException e){
                }
            }
        }
        if (jo.has("modes")){
            for (Iterator<String> it = jo.getJSONObject("modes").keys(); it.hasNext(); ) {
                String mode = it.next();
                JSONObject modeobj = jo.getJSONObject("modes").getJSONObject(mode);
                CryptoParam cpam = modeobj.length() == 0 ? new CryptoParam(mode) : new MultiCryptoParam(mode);
                cpam.loadFromJsonObject(modeobj);
                this.addPrimitive(cpam.getParamName(), cpam);
            }
        }

    }
}
