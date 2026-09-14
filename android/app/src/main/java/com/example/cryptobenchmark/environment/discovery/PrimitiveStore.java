package com.example.cryptobenchmark.environment.discovery;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

public class PrimitiveStore {

    protected Map<String, Set<String>> providers = new HashMap<>();

    protected Set<String> primitives = new HashSet<>(
    );

    protected Set<String> excluded_primitives = new HashSet<>(
    );

    public void addProviderForPrimitive(String primitiveName, String primitiveProvider){
        if(excluded_primitives.contains(primitiveName)){
            return;
        }
        if(this.providers.containsKey(primitiveName)){
            this.providers.get(primitiveName).add(primitiveProvider);
        }
        else{
            this.providers.put(primitiveName, new HashSet<>(Collections.singletonList(primitiveProvider)));
        }
    }

    public void addPrimitive(String primitiveName){
        if (excluded_primitives.contains(primitiveName)){
            return;
        }
        primitives.add(primitiveName);
    }

    public void removePrimitive(String primitiveName){
        if ( ! primitives.contains(primitiveName)){
            return;
        }
        primitives.remove(primitiveName);
    }

    public void addPrimitives(List<String> primitiveNames){
        for (String p : primitiveNames){
            addPrimitive(p);
        }
    }


}
