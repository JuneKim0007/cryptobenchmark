package com.example.cryptobenchmark.environment.discovery;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.HashSet;
import java.util.Iterator;
import java.util.Set;

public class MultiCryptoParam extends CryptoParam{

    private Set<CryptoParam> innerParams;
    private String paramName;

    public MultiCryptoParam(String paramName) {
        super(paramName);
        this.innerParams = new HashSet<>();
    }


    public Set<CryptoParam> getInnerParam() {
        return this.innerParams;
    }

    public void addParam(String id, CryptoParam cp){
        this.innerParams.add(cp);
    }

    public void loadFromJsonObject(JSONObject jo) throws JSONException {
        for (Iterator<String> it = jo.keys(); it.hasNext(); ) {
            String key = it.next();
            if(jo.get(key) instanceof JSONArray){
                for (int i = 0; i < jo.getJSONArray(key).length() ; i++) {
                    CryptoParam innerParam = new CryptoParam(jo.getJSONArray(key).getString(i));
                    this.addParam(innerParam.getParamName(), innerParam);
                }
            }
            else if(jo.get(key) instanceof JSONObject){
                CryptoParam innerParam = new MultiCryptoParam(key);
                innerParam.loadFromJsonObject((JSONObject) jo.get(key));
                this.addParam(innerParam.getParamName(), innerParam);
            }
        }
    }
}
