package com.example.cryptobenchmark.misc;

import java.lang.reflect.Method;

public class Utils {

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

}
