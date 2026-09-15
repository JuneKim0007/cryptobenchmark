package io.github.junekim0007.cryptobench.discovery;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.List;
import java.util.Map;

/**
 * Turns a capture into JSON. org.json rather than YAML because Android ships it and the rest of
 * this project already uses it; the probe stays unaware that this class exists.
 */
public final class EnvironmentJsonWriter {

    public JSONObject toJson(CapturedEnvironment environment) throws JSONException {
        JSONObject document = new JSONObject();
        document.put("schemaVersion", environment.getSchemaVersion());
        document.put("capturedAtMillis", environment.getCapturedAtMillis());
        document.put("runtime", runtime(environment.getRuntime()));

        JSONArray providers = new JSONArray();
        for (ProviderEntry provider : environment.getProviders()) {
            providers.put(provider(provider));
        }
        document.put("providers", providers);
        return document;
    }

    public void write(CapturedEnvironment environment, File target) throws JSONException, IOException {
        File parent = target.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            throw new IOException("cannot create " + parent.getAbsolutePath());
        }
        Writer writer = new OutputStreamWriter(new FileOutputStream(target), "UTF-8");
        try {
            writer.write(toJson(environment).toString(2));
        } finally {
            writer.close();
        }
    }

    private static JSONObject runtime(RuntimeInfo runtime) throws JSONException {
        JSONObject json = new JSONObject();
        json.put("model", runtime.getModel());
        json.put("manufacturer", runtime.getManufacturer());
        json.put("hardware", runtime.getHardware());
        json.put("sdkInt", runtime.getSdkInt());
        json.put("release", runtime.getRelease());
        json.put("javaVersion", runtime.getJavaVersion());
        return json;
    }

    private static JSONObject provider(ProviderEntry provider) throws JSONException {
        JSONObject json = new JSONObject();
        json.put("name", provider.getName());
        json.put("version", provider.getVersion());
        json.put("precedence", provider.getPrecedence());
        json.put("info", provider.getInfo());
        json.put("usable", provider.isUsable());

        JSONArray services = new JSONArray();
        for (ServiceEntry service : provider.getServices()) {
            services.put(service(service));
        }
        json.put("services", services);

        if (!provider.getUnresolvedAliases().isEmpty()) {
            JSONObject unresolved = new JSONObject();
            for (Map.Entry<String, String> entry : provider.getUnresolvedAliases().entrySet()) {
                unresolved.put(entry.getKey(), entry.getValue());
            }
            json.put("unresolvedAliases", unresolved);
        }
        return json;
    }

    private static JSONObject service(ServiceEntry service) throws JSONException {
        JSONObject json = new JSONObject();
        json.put("type", service.getType());
        json.put("algorithm", service.getAlgorithm());
        json.put("className", service.getClassName());

        if (!service.getAliases().isEmpty()) {
            json.put("aliases", new JSONArray(service.getAliases()));
        }

        ServiceAttributes attributes = service.getAttributes();
        if (!attributes.isEmpty()) {
            JSONObject declared = new JSONObject();
            for (Map.Entry<String, Object> entry : attributes.document().entrySet()) {
                Object value = entry.getValue();
                declared.put(entry.getKey(), value instanceof List
                        ? new JSONArray((List<?>) value)
                        : value);
            }
            json.put("attributes", declared);
        }
        return json;
    }
}
