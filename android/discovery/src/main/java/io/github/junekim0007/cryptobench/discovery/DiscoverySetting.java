package io.github.junekim0007.cryptobench.discovery;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.SortedSet;
import java.util.TreeSet;

/**
 * What the benchmark needs from a capture: which in-scope services each provider answers, plus the
 * attributes that narrow the matrix. Built by {@link DiscoverySettingConverter}, never from the JCA.
 */
public final class DiscoverySetting {

    public static final int SCHEMA_VERSION = 1;

    private final int schemaVersion;
    private final long capturedAtMillis;
    private final Device device;
    private final List<ProviderSetting> providers;

    public DiscoverySetting(long capturedAtMillis, Device device, List<ProviderSetting> providers) {
        if (device == null) {
            throw new NullPointerException("device");
        }
        this.schemaVersion = SCHEMA_VERSION;
        this.capturedAtMillis = capturedAtMillis;
        this.device = device;
        List<ProviderSetting> ordered = providers == null
                ? new ArrayList<ProviderSetting>()
                : new ArrayList<ProviderSetting>(providers);
        Collections.sort(ordered, new Comparator<ProviderSetting>() {
            @Override
            public int compare(ProviderSetting left, ProviderSetting right) {
                return left.getPrecedence() - right.getPrecedence();
            }
        });
        this.providers = Collections.unmodifiableList(ordered);
    }

    /** Providers that answer this type and algorithm or alias, in search order. */
    public List<ProviderSetting> providersFor(String type, String algorithmOrAlias) {
        List<ProviderSetting> answering = new ArrayList<ProviderSetting>();
        for (ProviderSetting provider : providers) {
            if (provider.find(type, algorithmOrAlias) != null) {
                answering.add(provider);
            }
        }
        return Collections.unmodifiableList(answering);
    }

    /** Canonical algorithm names registered for a type, across every provider. */
    public SortedSet<String> algorithms(String type) {
        String wanted = ServiceKey.fold(type);
        SortedSet<String> names = new TreeSet<String>();
        for (ProviderSetting provider : providers) {
            for (ServiceSetting service : provider.getServices()) {
                if (ServiceKey.fold(service.getType()).equals(wanted)) {
                    names.add(service.getAlgorithm());
                }
            }
        }
        return Collections.unmodifiableSortedSet(names);
    }

    public int getSchemaVersion() {
        return schemaVersion;
    }

    public long getCapturedAtMillis() {
        return capturedAtMillis;
    }

    public Device getDevice() {
        return device;
    }

    public List<ProviderSetting> getProviders() {
        return providers;
    }

    /** The device a setting describes. */
    public static final class Device {

        private final String model;
        private final String manufacturer;
        private final String hardware;
        private final int sdkInt;
        private final String release;

        public Device(String model, String manufacturer, String hardware, int sdkInt, String release) {
            this.model = model == null ? "" : model;
            this.manufacturer = manufacturer == null ? "" : manufacturer;
            this.hardware = hardware == null ? "" : hardware;
            this.sdkInt = sdkInt;
            this.release = release == null ? "" : release;
        }

        public String getModel() {
            return model;
        }

        public String getManufacturer() {
            return manufacturer;
        }

        public String getHardware() {
            return hardware;
        }

        public int getSdkInt() {
            return sdkInt;
        }

        public String getRelease() {
            return release;
        }
    }

    /** One provider, reduced to its in-scope services. */
    public static final class ProviderSetting {

        private final String name;
        private final String version;
        private final int precedence;
        private final List<ServiceSetting> services;
        private final Map<ServiceKey, ServiceSetting> byNameOrAlias;

        public ProviderSetting(String name, String version, int precedence, List<ServiceSetting> services) {
            if (name == null) {
                throw new NullPointerException("name");
            }
            this.name = name;
            this.version = version == null ? "" : version;
            this.precedence = precedence;
            this.services = services == null
                    ? Collections.<ServiceSetting>emptyList()
                    : Collections.unmodifiableList(new ArrayList<ServiceSetting>(services));

            Map<ServiceKey, ServiceSetting> index = new HashMap<ServiceKey, ServiceSetting>();
            for (ServiceSetting service : this.services) {
                index.put(ServiceKey.of(service.getType(), service.getAlgorithm()), service);
                for (String alias : service.getAliases()) {
                    index.put(ServiceKey.of(service.getType(), alias), service);
                }
            }
            this.byNameOrAlias = Collections.unmodifiableMap(index);
        }

        /** The service answering this type and algorithm or alias, or null. Case-insensitive. */
        public ServiceSetting find(String type, String algorithmOrAlias) {
            return byNameOrAlias.get(ServiceKey.of(type, algorithmOrAlias));
        }

        public String getName() {
            return name;
        }

        public String getVersion() {
            return version;
        }

        public int getPrecedence() {
            return precedence;
        }

        /** True when at least one in-scope service remains after conversion. */
        public boolean isUsable() {
            return !services.isEmpty();
        }

        public List<ServiceSetting> getServices() {
            return services;
        }
    }

    /** One in-scope service with the attributes that narrow the benchmark matrix. */
    public static final class ServiceSetting {

        private final String type;
        private final String algorithm;
        private final List<String> aliases;
        private final List<String> supportedModes;
        private final List<String> supportedPaddings;
        private final Integer keySize;

        public ServiceSetting(String type, String algorithm, List<String> aliases,
                              List<String> supportedModes, List<String> supportedPaddings, Integer keySize) {
            if (type == null) {
                throw new NullPointerException("type");
            }
            if (algorithm == null) {
                throw new NullPointerException("algorithm");
            }
            this.type = type;
            this.algorithm = algorithm;
            this.aliases = copy(aliases);
            this.supportedModes = copy(supportedModes);
            this.supportedPaddings = copy(supportedPaddings);
            this.keySize = keySize;
        }

        private static List<String> copy(List<String> values) {
            return values == null || values.isEmpty()
                    ? Collections.<String>emptyList()
                    : Collections.unmodifiableList(new ArrayList<String>(values));
        }

        public String getType() {
            return type;
        }

        public String getAlgorithm() {
            return algorithm;
        }

        public List<String> getAliases() {
            return aliases;
        }

        /** Empty when the provider does not declare it, not when it supports none. */
        public List<String> getSupportedModes() {
            return supportedModes;
        }

        /** Empty when the provider does not declare it, not when it supports none. */
        public List<String> getSupportedPaddings() {
            return supportedPaddings;
        }

        /** Largest declared key size, or null when undeclared. */
        public Integer getKeySize() {
            return keySize;
        }
    }
}
