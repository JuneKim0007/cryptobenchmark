package com.example.cryptobenchmark.misc;

import android.app.Application;

import org.json.JSONObject;

import java.lang.reflect.Method;
import java.security.MessageDigest;
import java.security.Provider;
import java.security.Security;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public class Utils {

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

    private static Application getApplicationUsingReflection() throws Exception {
        return (Application) Class.forName("android.app.ActivityThread")
                .getMethod("currentApplication").invoke(null, (Object[]) null);
    }

    public JSONObject loadJSONFromFile(String filename) {
        return new JSONObject();
    }

}
