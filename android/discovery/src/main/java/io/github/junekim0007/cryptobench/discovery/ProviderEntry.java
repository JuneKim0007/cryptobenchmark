package io.github.junekim0007.cryptobench.discovery;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** One installed provider, at its position in the preference order. */
public final class ProviderEntry {

    private static final Comparator<ServiceEntry> CANONICAL = new Comparator<ServiceEntry>() {
        @Override
        public int compare(ServiceEntry left, ServiceEntry right) {
            int byType = left.getType().compareTo(right.getType());
            return byType != 0 ? byType : left.getAlgorithm().compareTo(right.getAlgorithm());
        }
    };

    private final String name;
    private final String version;
    private final int precedence;
    private final String info;
    private final boolean usable;
    private final List<ServiceEntry> services;
    private final Map<String, String> unresolvedAliases;

    public ProviderEntry(String name, String version, int precedence, String info,
                         boolean usable, List<ServiceEntry> services,
                         Map<String, String> unresolvedAliases) {
        if (name == null) {
            throw new NullPointerException("name");
        }
        this.name = name;
        this.version = version == null ? "" : version;
        this.precedence = precedence;
        this.info = info == null ? "" : info;
        this.usable = usable;
        List<ServiceEntry> sorted = services == null
                ? new ArrayList<ServiceEntry>()
                : new ArrayList<ServiceEntry>(services);
        Collections.sort(sorted, CANONICAL);
        this.services = Collections.unmodifiableList(sorted);
        this.unresolvedAliases = unresolvedAliases == null || unresolvedAliases.isEmpty()
                ? Collections.<String, String>emptyMap()
                : Collections.unmodifiableMap(new TreeMap<String, String>(unresolvedAliases));
    }

    /** Registered but empty means present and unusable, as a Keystore provider without the hardware is. */
    public static boolean usableWith(List<ServiceEntry> services) {
        return services != null && !services.isEmpty();
    }

    public String getName() {
        return name;
    }

    public String getVersion() {
        return version;
    }

    /** 1-based position in Security.getProviders(), which is the order getInstance searches. */
    public int getPrecedence() {
        return precedence;
    }

    public String getInfo() {
        return info;
    }

    public boolean isUsable() {
        return usable;
    }

    public List<ServiceEntry> getServices() {
        return services;
    }

    /** Aliases whose target service is not registered: recorded rather than silently dropped. */
    public Map<String, String> getUnresolvedAliases() {
        return unresolvedAliases;
    }

    @Override
    public String toString() {
        return precedence + ":" + name;
    }
}
