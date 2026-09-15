package io.github.junekim0007.cryptobench.discovery;

import java.security.Provider;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/**
 * Reads the JCA. Knows nothing about JSON, and nothing about the benchmark.
 *
 * <p>Walks the provider property map rather than {@code getServices()} alone, because
 * {@code getServices()} returns neither aliases nor attributes: {@code SupportedModes},
 * {@code SupportedPaddings} and {@code KeySize} are declared as properties, and an alias such as
 * {@code Alg.Alias.Cipher.RC4 -> ARC4} is one implementation under a second name, not a second
 * implementation.
 */
public final class ProviderProbe {

    /** One "Alg.Alias.<type>.<name> = <target>" entry. */
    private static final class Alias {
        private final String type;
        private final String name;
        private final String target;

        Alias(String type, String name, String target) {
            this.type = type;
            this.name = name;
            this.target = target;
        }

        ServiceKey targetKey() {
            return ServiceKey.of(type, target);
        }
    }

    public CapturedEnvironment capture(Provider[] providers) {
        return capture(providers, RuntimeInfo.unknown(), System.currentTimeMillis());
    }

    public CapturedEnvironment capture(Provider[] providers, RuntimeInfo runtime) {
        return capture(providers, runtime, System.currentTimeMillis());
    }

    /** Timestamp is a parameter so a test can assert on a byte-stable document. */
    public CapturedEnvironment capture(Provider[] providers, RuntimeInfo runtime, long capturedAtMillis) {
        List<ProviderEntry> entries = new ArrayList<ProviderEntry>();
        if (providers != null) {
            for (int i = 0; i < providers.length; i++) {
                entries.add(toEntry(providers[i], i + 1));
            }
        }
        return new CapturedEnvironment(
                CapturedEnvironment.SCHEMA_VERSION, capturedAtMillis, runtime, entries);
    }

    private ProviderEntry toEntry(Provider provider, int precedence) {
        List<Alias> aliases = new ArrayList<Alias>();
        Map<ServiceKey, Map<String, Object>> attributes = new HashMap<ServiceKey, Map<String, Object>>();
        index(provider, aliases, attributes);

        Map<ServiceKey, List<String>> byTarget = new HashMap<ServiceKey, List<String>>();
        for (Alias alias : aliases) {
            ServiceKey key = alias.targetKey();
            List<String> names = byTarget.get(key);
            if (names == null) {
                names = new ArrayList<String>();
                byTarget.put(key, names);
            }
            names.add(alias.name);
        }

        List<ServiceEntry> services = new ArrayList<ServiceEntry>();
        Set<ServiceKey> present = new HashSet<ServiceKey>();
        for (Provider.Service service : provider.getServices()) {
            ServiceKey key = ServiceKey.of(service.getType(), service.getAlgorithm());
            present.add(key);
            Map<String, Object> declared = attributes.get(key);
            services.add(ServiceEntry.of(
                    service.getType(),
                    service.getAlgorithm(),
                    service.getClassName(),
                    byTarget.get(key),
                    declared == null ? new TreeMap<String, Object>() : declared));
        }

        Map<String, String> unresolved = new TreeMap<String, String>();
        for (Alias alias : aliases) {
            if (!present.contains(alias.targetKey())) {
                unresolved.put(alias.type + " " + alias.name, alias.target);
            }
        }

        return new ProviderEntry(
                provider.getName(),
                String.valueOf(provider.getVersion()),
                precedence,
                provider.getInfo(),
                ProviderEntry.usableWith(services),
                services,
                unresolved);
    }

    private static void index(Provider provider,
                              List<Alias> aliases,
                              Map<ServiceKey, Map<String, Object>> attributes) {
        for (String raw : provider.stringPropertyNames()) {
            PropertyKey key = PropertyKey.classify(raw);
            String value = provider.getProperty(raw);
            switch (key.getKind()) {
                case ALIAS:
                    aliases.add(new Alias(key.getType(), key.getAttribute(), value));
                    break;
                case ATTRIBUTE:
                    ServiceKey serviceKey = key.serviceKey();
                    Map<String, Object> bucket = attributes.get(serviceKey);
                    if (bucket == null) {
                        bucket = new TreeMap<String, Object>();
                        attributes.put(serviceKey, bucket);
                    }
                    bucket.put(key.getAttribute(), parseOrRaw(key.getAttribute(), value));
                    break;
                case PROVIDER_META:
                case SERVICE_IMPL:
                case MALFORMED:
                default:
                    break;
            }
        }
    }

    /** Capture records what is there; only an unparseable number is kept raw, for a reader to judge. */
    private static Object parseOrRaw(String attribute, String value) {
        try {
            return AttributeKind.parse(attribute, value);
        } catch (NumberFormatException e) {
            return value;
        }
    }
}
