package com.example.cryptobenchmark.environment.discovery;

import java.util.Locale;

/** Composite because algorithm names contain '/', '.', ':' and '#', so no flat string id is safe. */
public final class ServiceKey {

    private final String type;
    private final String algorithm;

    private ServiceKey(String type, String algorithm) {
        this.type = type;
        this.algorithm = algorithm;
    }

    public static ServiceKey of(String type, String algorithm) {
        return new ServiceKey(fold(type), fold(algorithm));
    }

    /**
     * Locale.ROOT or a Turkish-locale device folds "Cipher" to "CIPHER" with a dotted I and stops
     * matching. On Android the default locale is the user's, so this is not hypothetical.
     */
    private static String fold(String value) {
        return value == null ? null : value.toUpperCase(Locale.ROOT);
    }

    public String getType() {
        return type;
    }

    public String getAlgorithm() {
        return algorithm;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof ServiceKey)) {
            return false;
        }
        ServiceKey that = (ServiceKey) other;
        return (type == null ? that.type == null : type.equals(that.type))
                && (algorithm == null ? that.algorithm == null : algorithm.equals(that.algorithm));
    }

    @Override
    public int hashCode() {
        int result = type == null ? 0 : type.hashCode();
        return 31 * result + (algorithm == null ? 0 : algorithm.hashCode());
    }

    @Override
    public String toString() {
        return type + "." + algorithm;
    }
}
