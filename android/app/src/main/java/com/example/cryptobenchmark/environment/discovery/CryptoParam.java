package com.example.cryptobenchmark.environment.discovery;

import org.json.JSONException;
import org.json.JSONObject;

public class CryptoParam {

    private String paramName;

    enum PARAM_TYPE{
        MODE("mode"),
        PADDING("padding");

        public final String label;

        PARAM_TYPE(String label) {
            this.label = label;
        }
    }

    public CryptoParam(String paramName) {
        this.paramName = paramName;
    }

    public String getParamName() {
        return paramName;
    }

    public void loadFromJsonObject(JSONObject jo) throws JSONException {
    }
}
