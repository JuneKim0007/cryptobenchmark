package com.example.cryptobenchmark.environment.discovery;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/** One service as the provider declares it: what it is, plus every alias and attribute it carries. */
public final class ServiceEntry {

    private final String type;
    private final String algorithm;
    private final String className;
    private final List<String> aliases;
    private final ServiceAttributes attributes;

    /** Canonical order lives here so a capture is byte-stable and two devices can be diffed. */
    public ServiceEntry(String type, String algorithm, String className,
                        List<String> aliases, ServiceAttributes attributes) {
        if (type == null) {
            throw new NullPointerException("type");
        }
        if (algorithm == null) {
            throw new NullPointerException("algorithm");
        }
        this.type = type;
        this.algorithm = algorithm;
        this.className = className == null ? "" : className;
        List<String> sorted = aliases == null
                ? new ArrayList<String>()
                : new ArrayList<String>(aliases);
        Collections.sort(sorted);
        this.aliases = Collections.unmodifiableList(sorted);
        this.attributes = attributes == null ? ServiceAttributes.empty() : attributes;
    }

    public static ServiceEntry of(String type, String algorithm, String className,
                                  List<String> aliases, Map<String, Object> attributes) {
        return new ServiceEntry(type, algorithm, className, aliases, ServiceAttributes.of(attributes));
    }

    public String getType() {
        return type;
    }

    public String getAlgorithm() {
        return algorithm;
    }

    public String getClassName() {
        return className;
    }

    public List<String> getAliases() {
        return aliases;
    }

    public ServiceAttributes getAttributes() {
        return attributes;
    }

    public ServiceKey key() {
        return ServiceKey.of(type, algorithm);
    }

    @Override
    public String toString() {
        return type + "." + algorithm;
    }
}
