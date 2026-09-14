package com.example.cryptobenchmark.environment.discovery;


import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.Iterator;

public class CryptoPrimitive {

    private String primitiveName;
    private PrimitiveType primitiveType;
    private String simpleName;

    public enum PrimitiveType {
        DIGEST("digest"),
        SYMMETRIC_ENCRYPT("symmetric"),
        ASSYMMETRIC_ENCRYPT("assymetric"),
        MAC("mac"),
        SIGN("sign"),
        VERIFY("verify"),
        UNKNOWN("unknown");

        public final String label;

        PrimitiveType(String label) {
            this.label = label;
        }
    }

    public CryptoPrimitive(String name){
        this.primitiveName = name;
        this.primitiveType = PrimitiveType.UNKNOWN;
        this.simpleName = name;
    }

    public String getPrimitiveName() {
        return primitiveName;
    }

    public void setPrimitiveName(String primitiveName) {
        this.primitiveName = primitiveName;
    }

    public CryptoPrimitive(String primitiveName, PrimitiveType primitiveType) {
        this.primitiveName = primitiveName;
        this.primitiveType = primitiveType;
        this.simpleName = primitiveName;
    }

    public CryptoPrimitive(String primitiveName, String simpleName) {
        this.primitiveName = primitiveName;
        this.primitiveType = PrimitiveType.UNKNOWN;
        this.simpleName = simpleName;
    }

    public CryptoPrimitive(String primitiveName, PrimitiveType primitiveType, String simpleName) {
        this.primitiveName = primitiveName;
        this.primitiveType = primitiveType;
        this.simpleName = simpleName;
    }

    public String getSimpleName() {
        return simpleName;
    }

    public void setSimpleName(String fullPrimitiveDefinition) {
        this.simpleName = fullPrimitiveDefinition;
    }

    public void setPrimitiveType(PrimitiveType primitiveType) {
        this.primitiveType = primitiveType;
    }

    public void setPrimitiveType(String primitiveType) {
        this.primitiveType = PrimitiveType.valueOf(primitiveType);
    }

    public void loadFromJsonObject(JSONObject jo) throws JSONException {
        if(jo.has("type")){
            this.setPrimitiveType(jo.getString("type"));
        }
    }
}
