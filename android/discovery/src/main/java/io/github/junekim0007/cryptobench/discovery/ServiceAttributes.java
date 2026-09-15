package io.github.junekim0007.cryptobench.discovery;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/** Typed so the attribute rules stay here and no consumer has to instanceof its way through a map. */
public final class ServiceAttributes {

    private static final ServiceAttributes EMPTY =
            new ServiceAttributes(Collections.<String, Object>emptyMap());

    private final Map<String, Object> values;

    private ServiceAttributes(Map<String, Object> values) {
        this.values = values;
    }

    public static ServiceAttributes empty() {
        return EMPTY;
    }

    public static ServiceAttributes of(Map<String, Object> values) {
        if (values == null || values.isEmpty()) {
            return EMPTY;
        }
        return new ServiceAttributes(
                Collections.unmodifiableMap(new TreeMap<String, Object>(values)));
    }

    public boolean isEmpty() {
        return values.isEmpty();
    }

    public Set<String> names() {
        return values.keySet();
    }

    /** Declared largest key size, when the provider bothers to declare it. */
    public Integer keySize() {
        return integer("KeySize");
    }

    public List<String> supportedModes() {
        return strings("SupportedModes");
    }

    public List<String> supportedPaddings() {
        return strings("SupportedPaddings");
    }

    public List<String> supportedKeyClasses() {
        return strings("SupportedKeyClasses");
    }

    public List<String> supportedKeyFormats() {
        return strings("SupportedKeyFormats");
    }

    public List<String> supportedCurves() {
        return strings("SupportedCurves");
    }

    public boolean threadSafe() {
        Object value = values.get("ThreadSafe");
        return value instanceof Boolean && ((Boolean) value).booleanValue();
    }

    /** Escape hatch for vendor attributes this build does not model. */
    public String text(String name) {
        Object value = values.get(name);
        return value instanceof String ? (String) value : null;
    }

    public Integer integer(String name) {
        Object value = values.get(name);
        return value instanceof Integer ? (Integer) value : null;
    }

    @SuppressWarnings("unchecked")
    public List<String> strings(String name) {
        Object value = values.get(name);
        if (!(value instanceof List)) {
            return Collections.emptyList();
        }
        return Collections.unmodifiableList((List<String>) value);
    }

    /** The document view, for the codecs in this package only. */
    Map<String, Object> document() {
        return new LinkedHashMap<String, Object>(values);
    }

    @Override
    public boolean equals(Object other) {
        return other instanceof ServiceAttributes && values.equals(((ServiceAttributes) other).values);
    }

    @Override
    public int hashCode() {
        return values.hashCode();
    }

    @Override
    public String toString() {
        return values.toString();
    }
}
